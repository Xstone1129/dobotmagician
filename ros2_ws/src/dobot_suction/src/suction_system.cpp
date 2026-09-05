#include <chrono>
#include <cmath>
#include <mutex>
#include <string>
#include <gz/common/Console.hh>
#include <gz/msgs/boolean.pb.h>
#include <gz/msgs/empty.pb.h>
#include <gz/msgs/stringmsg.pb.h>
#include <gz/plugin/Register.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/System.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/components/Collision.hh>
#include <gz/sim/components/ContactSensorData.hh>
#include <gz/sim/components/DetachableJoint.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/transport/Node.hh>

namespace dobot {
class SuctionSystem : public gz::sim::System,
                      public gz::sim::ISystemConfigure,
                      public gz::sim::ISystemPreUpdate {
 public:
  void Configure(const gz::sim::Entity &entity,
                 const std::shared_ptr<const sdf::Element> &sdf,
                 gz::sim::EntityComponentManager &ecm,
                 gz::sim::EventManager &) override {
    model_ = entity;
    if (!gz::sim::Model(model_).Valid(ecm)) {
      gzerr << "SuctionSystem must be attached to the robot model.\n";
      return;
    }
    const auto link = sdf->Get<std::string>("link_name", "suction_cup_link").first;
    const auto collision = sdf->Get<std::string>(
        "collision_name", "suction_contact_collision").first;
    targetModel_ = sdf->Get<std::string>("target_model", "pick_box").first;
    surfaceZ_ = sdf->Get<double>("surface_z", -0.006).first;
    tip_ = gz::sim::Model(model_).LinkByName(ecm, link);
    collision_ = ecm.EntityByComponents(gz::sim::components::Collision(),
        gz::sim::components::ParentEntity(tip_),
        gz::sim::components::Name(collision));
    if (tip_ == gz::sim::kNullEntity || collision_ == gz::sim::kNullEntity) {
      gzerr << "Suction: missing link " << link << " or collision " << collision
            << ". Preserve the cup fixed joint during URDF conversion.\n";
      return;
    }
    if (!ecm.Component<gz::sim::components::ContactSensorData>(collision_))
      ecm.CreateComponent(collision_, gz::sim::components::ContactSensorData());
    const auto topic = sdf->Get<std::string>(
        "suction_topic", "/dobot_magician/suction/enable").first;
    node_.Subscribe(topic, &SuctionSystem::SetEnabled, this);
    // Retain the existing command topics for external callers.
    node_.Subscribe("/dobot_magician/attach", &SuctionSystem::Enable, this);
    node_.Subscribe("/dobot_magician/detach", &SuctionSystem::Release, this);
    state_ = node_.Advertise<gz::msgs::StringMsg>("/dobot_magician/suction_state");
    valid_ = true;
    gzmsg << "Suction: bottom-face contact on " << link << "; initially off.\n";
  }

  void PreUpdate(const gz::sim::UpdateInfo &info,
                 gz::sim::EntityComponentManager &ecm) override {
    if (!valid_ || info.paused) return;
    bool enabled, release;
    {
      std::lock_guard<std::mutex> lock(commandMutex_);
      enabled = enabled_;
      release = releaseRequested_;
      releaseRequested_ = false;
    }
    if (joint_ != gz::sim::kNullEntity &&
        (release || !ecm.HasEntity(target_) || !ecm.HasEntity(joint_))) {
      ecm.RequestRemoveEntity(joint_);
      joint_ = gz::sim::kNullEntity;
      target_ = gz::sim::kNullEntity;
      gzmsg << "Suction: detached\n";
    }
    // Leave a physics update between removal and any subsequent attachment.
    if (enabled && !release && joint_ == gz::sim::kNullEntity) {
      const auto contacts =
          ecm.Component<gz::sim::components::ContactSensorData>(collision_);
      if (contacts) {
        const auto cupPose = gz::sim::worldPose(tip_, ecm);
        const auto down = cupPose.Rot().RotateVector(gz::math::Vector3d(0, 0, -1));
        for (const auto &contact : contacts->Data().contact()) {
          if (contact.collision1().id() != collision_ &&
              contact.collision2().id() != collision_) continue;
          const auto other = contact.collision1().id() == collision_
              ? contact.collision2().id() : contact.collision1().id();
          const auto otherLink = ecm.ParentEntity(other);
          const auto otherModel = ecm.ParentEntity(otherLink);
          const gz::sim::Model candidate(otherModel);
          if (otherModel == model_ || !candidate.Valid(ecm) ||
              candidate.Static(ecm) || candidate.Name(ecm) != targetModel_) continue;
          bool bottomContact = false;
          for (int i = 0; i < contact.position_size() && i < contact.normal_size(); ++i) {
            const auto &p = contact.position(i);
            const auto &n = contact.normal(i);
            const auto local = cupPose.Rot().RotateVectorReverse(
                gz::math::Vector3d(p.x(), p.y(), p.z()) - cupPose.Pos());
            const gz::math::Vector3d normal(n.x(), n.y(), n.z());
            // Contact normals may point either way, depending on collision order.
            if (std::abs(local.Z() - surfaceZ_) <= 0.001 &&
                std::abs(normal.Dot(down)) >= 0.9) {
              bottomContact = true;
              break;
            }
          }
          if (!bottomContact) continue;
          joint_ = ecm.CreateEntity();
          ecm.CreateComponent(joint_, gz::sim::components::DetachableJoint(
              {tip_, otherLink, "fixed"}));
          target_ = otherLink;
          gzmsg << "Suction: bottom contact, attached to " << targetModel_ << "\n";
          break;
        }
      }
    }
    if (info.simTime >= nextPublish_) {
      nextPublish_ = info.simTime + std::chrono::milliseconds(100);
      gz::msgs::StringMsg msg;
      msg.set_data(joint_ == gz::sim::kNullEntity ? "detached" : "attached");
      state_.Publish(msg);
    }
  }

 private:
  void Command(bool enabled) {
    std::lock_guard<std::mutex> lock(commandMutex_);
    enabled_ = enabled;
    if (!enabled) releaseRequested_ = true;
  }
  void SetEnabled(const gz::msgs::Boolean &msg) { Command(msg.data()); }
  void Enable(const gz::msgs::Empty &) { Command(true); }
  void Release(const gz::msgs::Empty &) { Command(false); }
  gz::transport::Node node_;
  gz::transport::Node::Publisher state_;
  gz::sim::Entity model_{gz::sim::kNullEntity}, tip_{gz::sim::kNullEntity};
  gz::sim::Entity collision_{gz::sim::kNullEntity}, target_{gz::sim::kNullEntity};
  gz::sim::Entity joint_{gz::sim::kNullEntity};
  std::mutex commandMutex_;
  bool enabled_{false}, releaseRequested_{false}, valid_{false};
  double surfaceZ_{-0.006};
  std::string targetModel_;
  std::chrono::steady_clock::duration nextPublish_{};
};
}  // namespace dobot
GZ_ADD_PLUGIN(dobot::SuctionSystem, gz::sim::System,
              dobot::SuctionSystem::ISystemConfigure,
              dobot::SuctionSystem::ISystemPreUpdate)
