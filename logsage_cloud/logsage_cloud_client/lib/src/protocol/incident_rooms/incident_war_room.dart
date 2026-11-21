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
import 'package:serverpod_client/serverpod_client.dart' as _isc;

abstract class IncidentWarRoom
    implements _isc.SerializableModel, _isc.ProtocolSerialization {
  IncidentWarRoom._({
    this.id,
    required this.incidentId,
    required this.incidentTitle,
    required this.joinCode,
    required this.createdByUserId,
    required this.createdAt,
    this.closedAt,
  });

  factory IncidentWarRoom({
    int? id,
    required String incidentId,
    required String incidentTitle,
    required String joinCode,
    required String createdByUserId,
    required DateTime createdAt,
    DateTime? closedAt,
  }) = _IncidentWarRoomImpl;

  factory IncidentWarRoom.fromJson(Map<String, dynamic> jsonSerialization) {
    return IncidentWarRoom(
      id: jsonSerialization['id'] as int?,
      incidentId: jsonSerialization['incidentId'] as String,
      incidentTitle: jsonSerialization['incidentTitle'] as String,
      joinCode: jsonSerialization['joinCode'] as String,
      createdByUserId: jsonSerialization['createdByUserId'] as String,
      createdAt: _isc.DateTimeJsonExtension.fromJson(
        jsonSerialization['createdAt'],
      ),
      closedAt: jsonSerialization['closedAt'] == null
          ? null
          : _isc.DateTimeJsonExtension.fromJson(jsonSerialization['closedAt']),
    );
  }

  /// The database id, set if the object has been inserted into the
  /// database or if it has been fetched from the database. Otherwise,
  /// the id will be null.
  int? id;

  String incidentId;

  String incidentTitle;

  String joinCode;

  String createdByUserId;

  DateTime createdAt;

  DateTime? closedAt;

  /// Returns a shallow copy of this [IncidentWarRoom]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  IncidentWarRoom copyWith({
    int? id,
    String? incidentId,
    String? incidentTitle,
    String? joinCode,
    String? createdByUserId,
    DateTime? createdAt,
    DateTime? closedAt = const _isc.$UndefinedDateTime(),
  });
  @override
  Map<String, dynamic> toJson() {
    return {
      '__className__': 'IncidentWarRoom',
      if (id != null) 'id': id,
      'incidentId': incidentId,
      'incidentTitle': incidentTitle,
      'joinCode': joinCode,
      'createdByUserId': createdByUserId,
      'createdAt': createdAt.toJson(),
      if (closedAt != null) 'closedAt': closedAt?.toJson(),
    };
  }

  @override
  Map<String, dynamic> toJsonForProtocol() {
    return {
      '__className__': 'IncidentWarRoom',
      if (id != null) 'id': id,
      'incidentId': incidentId,
      'incidentTitle': incidentTitle,
      'joinCode': joinCode,
      'createdByUserId': createdByUserId,
      'createdAt': createdAt.toJson(),
      if (closedAt != null) 'closedAt': closedAt?.toJson(),
    };
  }

  @override
  String toString() {
    return _isc.SerializationManager.encode(this);
  }
}

class _Undefined {}

class _IncidentWarRoomImpl extends IncidentWarRoom {
  _IncidentWarRoomImpl({
    int? id,
    required String incidentId,
    required String incidentTitle,
    required String joinCode,
    required String createdByUserId,
    required DateTime createdAt,
    DateTime? closedAt,
  }) : super._(
         id: id,
         incidentId: incidentId,
         incidentTitle: incidentTitle,
         joinCode: joinCode,
         createdByUserId: createdByUserId,
         createdAt: createdAt,
         closedAt: closedAt,
       );

  /// Returns a shallow copy of this [IncidentWarRoom]
  /// with some or all fields replaced by the given arguments.
  @_isc.useResult
  @override
  IncidentWarRoom copyWith({
    Object? id = _Undefined,
    String? incidentId,
    String? incidentTitle,
    String? joinCode,
    String? createdByUserId,
    DateTime? createdAt,
    DateTime? closedAt = const _isc.$UndefinedDateTime(),
  }) {
    return IncidentWarRoom(
      id: id is int? ? id : this.id,
      incidentId: incidentId ?? this.incidentId,
      incidentTitle: incidentTitle ?? this.incidentTitle,
      joinCode: joinCode ?? this.joinCode,
      createdByUserId: createdByUserId ?? this.createdByUserId,
      createdAt: createdAt ?? this.createdAt,
      closedAt: closedAt is _isc.UndefinedSentinel ? this.closedAt : closedAt,
    );
  }
}
