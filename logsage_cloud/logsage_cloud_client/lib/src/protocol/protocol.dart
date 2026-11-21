/* AUTOMATICALLY GENERATED CODE DO NOT MODIFY */
/*   To generate run: "serverpod generate"    */

// ignore_for_file: implementation_imports
// ignore_for_file: library_private_types_in_public_api
// ignore_for_file: non_constant_identifier_names
// ignore_for_file: public_member_api_docs
// ignore_for_file: type_literal_in_constant_pattern
// ignore_for_file: use_super_parameters
// ignore_for_file: invalid_use_of_internal_member
// ignore_for_file: dead_code, unnecessary_type_check

// ignore_for_file: no_leading_underscores_for_library_prefixes
import 'package:serverpod_auth_core_client/serverpod_auth_core_client.dart'
    as _iacc;
import 'package:serverpod_auth_idp_client/serverpod_auth_idp_client.dart'
    as _iaic;
import 'package:serverpod_client/serverpod_client.dart' as _isc;
import 'incident_rooms/incident_war_room.dart' as _iehq5onp;
import 'incident_rooms/room_activity.dart' as _iy6f39dt;
import 'incident_rooms/room_message.dart' as _iiu4yj18;
import 'incident_rooms/room_participant.dart' as _if9g2un2;
import 'incident_rooms/room_snapshot.dart' as _i36mz8w5;
export 'incident_rooms/incident_war_room.dart';
export 'incident_rooms/room_activity.dart';
export 'incident_rooms/room_message.dart';
export 'incident_rooms/room_participant.dart';
export 'incident_rooms/room_snapshot.dart';
export 'client.dart';

class Protocol extends _isc.SerializationManager
    implements _isc.ProtocolDeserializationProvider {
  Protocol._();

  factory Protocol() => _instance;

  static final Protocol _instance = Protocol._().._registerHostProtocols();

  @override
  _isc.ProtocolDeserialization get deserializationMetadata =>
      _isc.ProtocolDeserialization.cached(
        this,
        types: const [
          _isc.getType<_iehq5onp.IncidentWarRoom>,
          _isc.getType<_iy6f39dt.RoomActivity>,
          _isc.getType<_iiu4yj18.RoomMessage>,
          _isc.getType<_if9g2un2.RoomParticipant>,
          _isc.getType<_i36mz8w5.RoomSnapshot>,
          _isc.getType<_iehq5onp.IncidentWarRoom?>,
          _isc.getType<_iy6f39dt.RoomActivity?>,
          _isc.getType<_iiu4yj18.RoomMessage?>,
          _isc.getType<_if9g2un2.RoomParticipant?>,
          _isc.getType<_i36mz8w5.RoomSnapshot?>,
          _isc.getType<List<_if9g2un2.RoomParticipant>>,
          _isc.getType<List<_iiu4yj18.RoomMessage>>,
        ],
        modules: const [
          _iaic.Protocol.new,
          _iacc.Protocol.new,
        ],
        classNames: const [
          'IncidentWarRoom',
          'RoomActivity',
          'RoomMessage',
          'RoomParticipant',
          'RoomSnapshot',
        ],
      );

  static String? getClassNameFromObjectJson(dynamic data) =>
      _isc.ProtocolDeserialization.readClassName(data);

  @override
  T deserialize<T>(
    dynamic data, [
    Type? t,
  ]) {
    t ??= T;
    final rawDataClassName = _isc.ProtocolDeserialization.readClassName(data);
    final dataClassName = rawDataClassName;
    if (dataClassName != null && dataClassName != getClassNameForType(t)) {
      try {
        return deserializeByClassName({
          'className': dataClassName,
          'data': data,
        });
      } on _isc.DeserializationClassNameNotFoundException catch (_) {
        // If the className is not recognized (e.g., older client receiving
        // data with a new subtype), fall back to deserializing without the
        // className, using the expected type T.
      }
    }

    if (t == _iehq5onp.IncidentWarRoom) {
      return _iehq5onp.IncidentWarRoom.fromJson(data) as T;
    }
    if (t == _iy6f39dt.RoomActivity) {
      return _iy6f39dt.RoomActivity.fromJson(data) as T;
    }
    if (t == _iiu4yj18.RoomMessage) {
      return _iiu4yj18.RoomMessage.fromJson(data) as T;
    }
    if (t == _if9g2un2.RoomParticipant) {
      return _if9g2un2.RoomParticipant.fromJson(data) as T;
    }
    if (t == _i36mz8w5.RoomSnapshot) {
      return _i36mz8w5.RoomSnapshot.fromJson(data) as T;
    }
    if (t == _isc.getType<_iehq5onp.IncidentWarRoom?>()) {
      return (data != null ? _iehq5onp.IncidentWarRoom.fromJson(data) : null)
          as T;
    }
    if (t == _isc.getType<_iy6f39dt.RoomActivity?>()) {
      return (data != null ? _iy6f39dt.RoomActivity.fromJson(data) : null) as T;
    }
    if (t == _isc.getType<_iiu4yj18.RoomMessage?>()) {
      return (data != null ? _iiu4yj18.RoomMessage.fromJson(data) : null) as T;
    }
    if (t == _isc.getType<_if9g2un2.RoomParticipant?>()) {
      return (data != null ? _if9g2un2.RoomParticipant.fromJson(data) : null)
          as T;
    }
    if (t == _isc.getType<_i36mz8w5.RoomSnapshot?>()) {
      return (data != null ? _i36mz8w5.RoomSnapshot.fromJson(data) : null) as T;
    }
    if (t == List<_if9g2un2.RoomParticipant>) {
      return (data as List)
              .map((e) => deserialize<_if9g2un2.RoomParticipant>(e))
              .toList()
          as T;
    }
    if (t == List<_iiu4yj18.RoomMessage>) {
      return (data as List)
              .map((e) => deserialize<_iiu4yj18.RoomMessage>(e))
              .toList()
          as T;
    }
    final modules = deserializationMetadata.modulesForDeserialization(
      t,
      className: rawDataClassName,
    );
    for (final module in modules) {
      try {
        return module.deserialize<T>(data, t);
      } on _isc.DeserializationTypeNotFoundException catch (_) {}
    }

    return super.deserialize<T>(data, t);
  }

  static String? getClassNameForType(Type type) {
    return switch (type) {
      _iehq5onp.IncidentWarRoom => 'IncidentWarRoom',
      _iy6f39dt.RoomActivity => 'RoomActivity',
      _iiu4yj18.RoomMessage => 'RoomMessage',
      _if9g2un2.RoomParticipant => 'RoomParticipant',
      _i36mz8w5.RoomSnapshot => 'RoomSnapshot',
      _ => null,
    };
  }

  @override
  String? getClassNameForObject(Object? data) {
    String? className = super.getClassNameForObject(data);
    if (className != null) return className;

    if (data is Map<String, dynamic> && data['__className__'] is String) {
      return (data['__className__'] as String).replaceFirst(
        'logsage_cloud.',
        '',
      );
    }

    switch (data) {
      case _iehq5onp.IncidentWarRoom():
        return 'IncidentWarRoom';
      case _iy6f39dt.RoomActivity():
        return 'RoomActivity';
      case _iiu4yj18.RoomMessage():
        return 'RoomMessage';
      case _if9g2un2.RoomParticipant():
        return 'RoomParticipant';
      case _i36mz8w5.RoomSnapshot():
        return 'RoomSnapshot';
    }
    className = _iaic.Protocol().getClassNameForObject(data);
    if (className != null) {
      return className.contains('.')
          ? className
          : 'serverpod_auth_idp.$className';
    }
    className = _iacc.Protocol().getClassNameForObject(data);
    if (className != null) {
      return className.contains('.')
          ? className
          : 'serverpod_auth_core.$className';
    }
    return null;
  }

  @override
  dynamic deserializeByClassName(Map<String, dynamic> data) {
    var dataClassName = data['className'];
    if (dataClassName is! String) {
      return super.deserializeByClassName(data);
    }
    if (dataClassName == 'IncidentWarRoom') {
      return deserialize<_iehq5onp.IncidentWarRoom>(data['data']);
    }
    if (dataClassName == 'RoomActivity') {
      return deserialize<_iy6f39dt.RoomActivity>(data['data']);
    }
    if (dataClassName == 'RoomMessage') {
      return deserialize<_iiu4yj18.RoomMessage>(data['data']);
    }
    if (dataClassName == 'RoomParticipant') {
      return deserialize<_if9g2un2.RoomParticipant>(data['data']);
    }
    if (dataClassName == 'RoomSnapshot') {
      return deserialize<_i36mz8w5.RoomSnapshot>(data['data']);
    }
    if (dataClassName.startsWith('serverpod_auth_idp.')) {
      return _iaic.Protocol().deserializeByClassName({
        ...data,
        'className': dataClassName.substring(19),
      });
    }
    if (dataClassName.startsWith('serverpod_auth_core.')) {
      return _iacc.Protocol().deserializeByClassName({
        ...data,
        'className': dataClassName.substring(20),
      });
    }
    return super.deserializeByClassName(data);
  }

  void _registerHostProtocols() {
    _iaic.Protocol().registerHostProtocol('logsage_cloud', this);
    _iacc.Protocol().registerHostProtocol('logsage_cloud', this);
  }

  @override
  String getModuleName() => 'logsage_cloud';

  /// Maps any `Record`s known to this [Protocol] to their JSON representation
  ///
  /// Throws in case the record type is not known.
  ///
  /// This method will return `null` (only) for `null` inputs.
  Map<String, dynamic>? mapRecordToJson(Record? record) {
    if (record == null) {
      return null;
    }
    try {
      return _iaic.Protocol().mapRecordToJson(record);
    } catch (_) {}
    try {
      return _iacc.Protocol().mapRecordToJson(record);
    } catch (_) {}
    throw Exception('Unsupported record type ${record.runtimeType}');
  }
}
