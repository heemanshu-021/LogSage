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
import 'package:serverpod/protocol.dart' as _isp;
import 'package:serverpod/serverpod.dart' as _is;
import 'package:serverpod_auth_core_server/serverpod_auth_core_server.dart'
    as _iacs;
import 'package:serverpod_auth_idp_server/serverpod_auth_idp_server.dart'
    as _iais;
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

class Protocol extends _is.DatabaseSerializationManager
    implements _is.DatabaseProtocolDeserializationProvider {
  Protocol._();

  factory Protocol() => _instance;

  static final Protocol _instance = Protocol._().._registerHostProtocols();

  @override
  _is.ProtocolDeserialization get deserializationMetadata =>
      _is.ProtocolDeserialization.cached(
        this,
        types: const [
          _is.getType<_iehq5onp.IncidentWarRoom>,
          _is.getType<_iy6f39dt.RoomActivity>,
          _is.getType<_iiu4yj18.RoomMessage>,
          _is.getType<_if9g2un2.RoomParticipant>,
          _is.getType<_i36mz8w5.RoomSnapshot>,
          _is.getType<_iehq5onp.IncidentWarRoom?>,
          _is.getType<_iy6f39dt.RoomActivity?>,
          _is.getType<_iiu4yj18.RoomMessage?>,
          _is.getType<_if9g2un2.RoomParticipant?>,
          _is.getType<_i36mz8w5.RoomSnapshot?>,
          _is.getType<List<_if9g2un2.RoomParticipant>>,
          _is.getType<List<_iiu4yj18.RoomMessage>>,
        ],
        modules: const [
          _iais.Protocol.new,
          _iacs.Protocol.new,
          _isp.Protocol.new,
        ],
        classNames: const [
          'IncidentWarRoom',
          'RoomActivity',
          'RoomMessage',
          'RoomParticipant',
          'RoomSnapshot',
        ],
      );

  static List<_isp.TableDefinition> get targetTableDefinitions => [
    ..._ownTableDefinitions,
    ..._iais.Protocol().getOwnTableDefinitions(),
    ..._iacs.Protocol().getOwnTableDefinitions(),
    ..._isp.Protocol.targetTableDefinitions,
  ];

  static List<_isp.TableDefinition> get _ownTableDefinitions => [
    _isp.TableDefinition(
      name: 'incident_war_room',
      dartName: 'IncidentWarRoom',
      schema: 'public',
      module: 'logsage_cloud',
      columns: [
        _isp.ColumnDefinition(
          name: 'id',
          columnType: _isp.ColumnType.bigint,
          isNullable: false,
          dartType: 'int?',
          columnDefault: 'serial',
        ),
        _isp.ColumnDefinition(
          name: 'incidentId',
          columnType: _isp.ColumnType.text,
          isNullable: false,
          dartType: 'String',
        ),
        _isp.ColumnDefinition(
          name: 'incidentTitle',
          columnType: _isp.ColumnType.text,
          isNullable: false,
          dartType: 'String',
        ),
        _isp.ColumnDefinition(
          name: 'joinCode',
          columnType: _isp.ColumnType.text,
          isNullable: false,
          dartType: 'String',
        ),
        _isp.ColumnDefinition(
          name: 'createdByUserId',
          columnType: _isp.ColumnType.text,
          isNullable: false,
          dartType: 'String',
        ),
        _isp.ColumnDefinition(
          name: 'createdAt',
          columnType: _isp.ColumnType.timestampWithoutTimeZone,
          isNullable: false,
          dartType: 'DateTime',
        ),
        _isp.ColumnDefinition(
          name: 'closedAt',
          columnType: _isp.ColumnType.timestampWithoutTimeZone,
          isNullable: true,
          dartType: 'DateTime?',
        ),
      ],
      foreignKeys: [],
      indexes: [
        _isp.IndexDefinition(
          indexName: 'incident_war_room__joinCode__unique_idx',
          tableSpace: null,
          elements: [
            _isp.IndexElementDefinition(
              type: _isp.IndexElementDefinitionType.column,
              definition: 'joinCode',
            ),
          ],
          type: 'btree',
          isUnique: true,
          isPrimary: false,
        ),
        _isp.IndexDefinition(
          indexName: 'incident_war_room_incident_idx',
          tableSpace: null,
          elements: [
            _isp.IndexElementDefinition(
              type: _isp.IndexElementDefinitionType.column,
              definition: 'incidentId',
            ),
          ],
          type: 'btree',
          isUnique: false,
          isPrimary: false,
        ),
        _isp.IndexDefinition(
          indexName: 'incident_war_room_join_code_idx',
          tableSpace: null,
          elements: [
            _isp.IndexElementDefinition(
              type: _isp.IndexElementDefinitionType.column,
              definition: 'joinCode',
            ),
          ],
          type: 'btree',
          isUnique: true,
          isPrimary: false,
        ),
      ],
      managed: true,
    ),
    _isp.TableDefinition(
      name: 'room_message',
      dartName: 'RoomMessage',
      schema: 'public',
      module: 'logsage_cloud',
      columns: [
        _isp.ColumnDefinition(
          name: 'id',
          columnType: _isp.ColumnType.bigint,
          isNullable: false,
          dartType: 'int?',
          columnDefault: 'serial',
        ),
        _isp.ColumnDefinition(
          name: 'roomId',
          columnType: _isp.ColumnType.bigint,
          isNullable: false,
          dartType: 'int',
        ),
        _isp.ColumnDefinition(
          name: 'userIdentifier',
          columnType: _isp.ColumnType.text,
          isNullable: false,
          dartType: 'String',
        ),
        _isp.ColumnDefinition(
          name: 'authorName',
          columnType: _isp.ColumnType.text,
          isNullable: false,
          dartType: 'String',
        ),
        _isp.ColumnDefinition(
          name: 'content',
          columnType: _isp.ColumnType.text,
          isNullable: false,
          dartType: 'String',
        ),
        _isp.ColumnDefinition(
          name: 'createdAt',
          columnType: _isp.ColumnType.timestampWithoutTimeZone,
          isNullable: false,
          dartType: 'DateTime',
        ),
      ],
      foreignKeys: [
        _isp.ForeignKeyDefinition(
          constraintName: 'room_message_fk_0',
          columns: ['roomId'],
          referenceTable: 'incident_war_room',
          referenceTableSchema: 'public',
          referenceColumns: ['id'],
          onUpdate: _isp.ForeignKeyAction.noAction,
          onDelete: _isp.ForeignKeyAction.cascade,
          matchType: null,
        ),
      ],
      indexes: [
        _isp.IndexDefinition(
          indexName: 'room_message_room_created_idx',
          tableSpace: null,
          elements: [
            _isp.IndexElementDefinition(
              type: _isp.IndexElementDefinitionType.column,
              definition: 'roomId',
            ),
            _isp.IndexElementDefinition(
              type: _isp.IndexElementDefinitionType.column,
              definition: 'createdAt',
            ),
          ],
          type: 'btree',
          isUnique: false,
          isPrimary: false,
        ),
      ],
      managed: true,
    ),
    _isp.TableDefinition(
      name: 'room_participant',
      dartName: 'RoomParticipant',
      schema: 'public',
      module: 'logsage_cloud',
      columns: [
        _isp.ColumnDefinition(
          name: 'id',
          columnType: _isp.ColumnType.bigint,
          isNullable: false,
          dartType: 'int?',
          columnDefault: 'serial',
        ),
        _isp.ColumnDefinition(
          name: 'roomId',
          columnType: _isp.ColumnType.bigint,
          isNullable: false,
          dartType: 'int',
        ),
        _isp.ColumnDefinition(
          name: 'userIdentifier',
          columnType: _isp.ColumnType.text,
          isNullable: false,
          dartType: 'String',
        ),
        _isp.ColumnDefinition(
          name: 'displayName',
          columnType: _isp.ColumnType.text,
          isNullable: false,
          dartType: 'String',
        ),
        _isp.ColumnDefinition(
          name: 'joinedAt',
          columnType: _isp.ColumnType.timestampWithoutTimeZone,
          isNullable: false,
          dartType: 'DateTime',
        ),
        _isp.ColumnDefinition(
          name: 'lastSeenAt',
          columnType: _isp.ColumnType.timestampWithoutTimeZone,
          isNullable: false,
          dartType: 'DateTime',
        ),
      ],
      foreignKeys: [
        _isp.ForeignKeyDefinition(
          constraintName: 'room_participant_fk_0',
          columns: ['roomId'],
          referenceTable: 'incident_war_room',
          referenceTableSchema: 'public',
          referenceColumns: ['id'],
          onUpdate: _isp.ForeignKeyAction.noAction,
          onDelete: _isp.ForeignKeyAction.cascade,
          matchType: null,
        ),
      ],
      indexes: [
        _isp.IndexDefinition(
          indexName: 'room_participant_room_user_idx',
          tableSpace: null,
          elements: [
            _isp.IndexElementDefinition(
              type: _isp.IndexElementDefinitionType.column,
              definition: 'roomId',
            ),
            _isp.IndexElementDefinition(
              type: _isp.IndexElementDefinitionType.column,
              definition: 'userIdentifier',
            ),
          ],
          type: 'btree',
          isUnique: true,
          isPrimary: false,
        ),
      ],
      managed: true,
    ),
  ];

  static String? getClassNameFromObjectJson(dynamic data) =>
      _is.ProtocolDeserialization.readClassName(data);

  @override
  T deserialize<T>(
    dynamic data, [
    Type? t,
  ]) {
    t ??= T;
    final rawDataClassName = _is.ProtocolDeserialization.readClassName(data);
    final dataClassName = rawDataClassName;
    if (dataClassName != null && dataClassName != getClassNameForType(t)) {
      try {
        return deserializeByClassName({
          'className': dataClassName,
          'data': data,
        });
      } on _is.DeserializationClassNameNotFoundException catch (_) {
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
    if (t == _is.getType<_iehq5onp.IncidentWarRoom?>()) {
      return (data != null ? _iehq5onp.IncidentWarRoom.fromJson(data) : null)
          as T;
    }
    if (t == _is.getType<_iy6f39dt.RoomActivity?>()) {
      return (data != null ? _iy6f39dt.RoomActivity.fromJson(data) : null) as T;
    }
    if (t == _is.getType<_iiu4yj18.RoomMessage?>()) {
      return (data != null ? _iiu4yj18.RoomMessage.fromJson(data) : null) as T;
    }
    if (t == _is.getType<_if9g2un2.RoomParticipant?>()) {
      return (data != null ? _if9g2un2.RoomParticipant.fromJson(data) : null)
          as T;
    }
    if (t == _is.getType<_i36mz8w5.RoomSnapshot?>()) {
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
      } on _is.DeserializationTypeNotFoundException catch (_) {}
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
    className = _iais.Protocol().getClassNameForObject(data);
    if (className != null) {
      return className.contains('.')
          ? className
          : 'serverpod_auth_idp.$className';
    }
    className = _iacs.Protocol().getClassNameForObject(data);
    if (className != null) {
      return className.contains('.')
          ? className
          : 'serverpod_auth_core.$className';
    }
    className = _isp.Protocol().getClassNameForObject(data);
    if (className != null) {
      return className.contains('.') ? className : 'serverpod.$className';
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
      return _iais.Protocol().deserializeByClassName({
        ...data,
        'className': dataClassName.substring(19),
      });
    }
    if (dataClassName.startsWith('serverpod_auth_core.')) {
      return _iacs.Protocol().deserializeByClassName({
        ...data,
        'className': dataClassName.substring(20),
      });
    }
    if (dataClassName.startsWith('serverpod.')) {
      return _isp.Protocol().deserializeByClassName({
        ...data,
        'className': dataClassName.substring(10),
      });
    }
    return super.deserializeByClassName(data);
  }

  void _registerHostProtocols() {
    _iais.Protocol().registerHostProtocol('logsage_cloud', this);
    _iacs.Protocol().registerHostProtocol('logsage_cloud', this);
  }

  @override
  _is.Table? getTableForType(Type t) {
    {
      var table = _iais.Protocol().getTableForType(t);
      if (table != null) {
        return table;
      }
    }
    {
      var table = _iacs.Protocol().getTableForType(t);
      if (table != null) {
        return table;
      }
    }
    {
      var table = _isp.Protocol().getTableForType(t);
      if (table != null) {
        return table;
      }
    }
    switch (t) {
      case _iehq5onp.IncidentWarRoom:
        return _iehq5onp.IncidentWarRoom.t;
      case _iiu4yj18.RoomMessage:
        return _iiu4yj18.RoomMessage.t;
      case _if9g2un2.RoomParticipant:
        return _if9g2un2.RoomParticipant.t;
    }
    return null;
  }

  @override
  List<_isp.TableDefinition> getTargetTableDefinitions() =>
      targetTableDefinitions;

  @override
  List<_isp.TableDefinition> getOwnTableDefinitions() => _ownTableDefinitions;

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
      return _iais.Protocol().mapRecordToJson(record);
    } catch (_) {}
    try {
      return _iacs.Protocol().mapRecordToJson(record);
    } catch (_) {}
    throw Exception('Unsupported record type ${record.runtimeType}');
  }
}
