/* AUTOMATICALLY GENERATED CODE DO NOT MODIFY */
/*   To generate run: "serverpod generate"    */

// ignore_for_file: implementation_imports
// ignore_for_file: library_private_types_in_public_api
// ignore_for_file: non_constant_identifier_names
// ignore_for_file: public_member_api_docs
// ignore_for_file: type_literal_in_constant_pattern
// ignore_for_file: use_super_parameters
// ignore_for_file: invalid_use_of_internal_member

// ignore_for_file: no_leading_underscores_for_library_prefixes
import 'package:logsage_cloud_server/src/generated/protocol.dart' as _iwyzgx6p;
import 'package:serverpod/serverpod.dart' as _is;
import '../incident_rooms/incident_war_room.dart' as _iyhko5ec;
import '../incident_rooms/room_message.dart' as _ipkhtt20;
import '../incident_rooms/room_participant.dart' as _ig6bn0kx;

abstract class RoomSnapshot
    implements _is.SerializableModel, _is.ProtocolSerialization {
  RoomSnapshot._({
    required this.room,
    required this.participants,
    required this.messages,
  });

  factory RoomSnapshot({
    required _iyhko5ec.IncidentWarRoom room,
    required List<_ig6bn0kx.RoomParticipant> participants,
    required List<_ipkhtt20.RoomMessage> messages,
  }) = _RoomSnapshotImpl;

  factory RoomSnapshot.fromJson(Map<String, dynamic> jsonSerialization) {
    return RoomSnapshot(
      room: _iwyzgx6p.Protocol().deserialize<_iyhko5ec.IncidentWarRoom>(
        jsonSerialization['room'],
      ),
      participants: _iwyzgx6p.Protocol()
          .deserialize<List<_ig6bn0kx.RoomParticipant>>(
            jsonSerialization['participants'],
          ),
      messages: _iwyzgx6p.Protocol().deserialize<List<_ipkhtt20.RoomMessage>>(
        jsonSerialization['messages'],
      ),
    );
  }

  _iyhko5ec.IncidentWarRoom room;

  List<_ig6bn0kx.RoomParticipant> participants;

  List<_ipkhtt20.RoomMessage> messages;

  /// Returns a shallow copy of this [RoomSnapshot]
  /// with some or all fields replaced by the given arguments.
  @_is.useResult
  RoomSnapshot copyWith({
    _iyhko5ec.IncidentWarRoom? room,
    List<_ig6bn0kx.RoomParticipant>? participants,
    List<_ipkhtt20.RoomMessage>? messages,
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'RoomSnapshot',
      'room': room.toJson(),
      'participants': participants.toJson(valueToJson: (v) => v.toJson()),
      'messages': messages.toJson(valueToJson: (v) => v.toJson()),
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'RoomSnapshot',
      'room': room.toJsonForProtocol(),
      'participants': participants.toJson(
        valueToJson: (v) => v.toJsonForProtocol(),
      ),
      'messages': messages.toJson(valueToJson: (v) => v.toJsonForProtocol()),
    };
  }

  @override
  String toString() {
    return _is.SerializationManager.encode(this);
  }
}

class _RoomSnapshotImpl extends RoomSnapshot {
  _RoomSnapshotImpl({
    required _iyhko5ec.IncidentWarRoom room,
    required List<_ig6bn0kx.RoomParticipant> participants,
    required List<_ipkhtt20.RoomMessage> messages,
  }) : super._(
         room: room,
         participants: participants,
         messages: messages,
       );

  /// Returns a shallow copy of this [RoomSnapshot]
  /// with some or all fields replaced by the given arguments.
  @_is.useResult
  @override
  RoomSnapshot copyWith({
    _iyhko5ec.IncidentWarRoom? room,
    List<_ig6bn0kx.RoomParticipant>? participants,
    List<_ipkhtt20.RoomMessage>? messages,
  }) {
    return RoomSnapshot(
      room: room ?? this.room.copyWith(),
      participants:
          participants ?? this.participants.map((e0) => e0.copyWith()).toList(),
      messages: messages ?? this.messages.map((e0) => e0.copyWith()).toList(),
    );
  }
}
