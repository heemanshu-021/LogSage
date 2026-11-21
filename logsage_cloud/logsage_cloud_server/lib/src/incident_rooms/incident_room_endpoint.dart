import 'dart:math';

import 'package:serverpod/serverpod.dart';

import '../generated/protocol.dart';

/// Authenticated, real-time collaboration for one LogSage incident.
class IncidentRoomEndpoint extends Endpoint {
  static const _codeAlphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ';
  static const _maxParticipants = 100;
  static const _maxMessageLength = 2000;

  @override
  bool get requireLogin => true;

  Future<IncidentWarRoom> createRoom(
    Session session, {
    required String incidentId,
    required String incidentTitle,
    required String displayName,
  }) async {
    final userId = _userId(session);
    final normalizedIncidentId = incidentId.trim();
    final normalizedTitle = incidentTitle.trim();
    final normalizedName = _validateDisplayName(displayName);
    if (normalizedIncidentId.isEmpty || normalizedIncidentId.length > 120) {
      throw ArgumentError.value(
        incidentId,
        'incidentId',
        'Invalid incident ID.',
      );
    }
    if (normalizedTitle.isEmpty || normalizedTitle.length > 240) {
      throw ArgumentError.value(
        incidentTitle,
        'incidentTitle',
        'Invalid incident title.',
      );
    }

    final now = DateTime.now().toUtc();
    final room = await IncidentWarRoom.db.insertRow(
      session,
      IncidentWarRoom(
        incidentId: normalizedIncidentId,
        incidentTitle: normalizedTitle,
        joinCode: _newJoinCode(),
        createdByUserId: userId,
        createdAt: now,
        closedAt: null,
      ),
    );
    await RoomParticipant.db.insertRow(
      session,
      RoomParticipant(
        roomId: room.id!,
        userIdentifier: userId,
        displayName: normalizedName,
        joinedAt: now,
        lastSeenAt: now,
      ),
    );
    await _publish(
      session,
      room.id!,
      RoomActivity(
        kind: 'participant_joined',
        displayName: normalizedName,
        content: 'joined the incident room',
        createdAt: now,
      ),
    );
    return room;
  }

  Future<RoomSnapshot> joinRoom(
    Session session, {
    required String joinCode,
    required String displayName,
  }) async {
    final room = await _findOpenRoom(session, joinCode);
    final userId = _userId(session);
    final name = _validateDisplayName(displayName);
    final now = DateTime.now().toUtc();
    var participant = await RoomParticipant.db.findFirstRow(
      session,
      where: (t) => t.roomId.equals(room.id!) & t.userIdentifier.equals(userId),
    );

    final isNewParticipant = participant == null;
    if (participant == null) {
      final currentParticipants = await RoomParticipant.db.find(
        session,
        where: (t) => t.roomId.equals(room.id!),
        limit: _maxParticipants,
      );
      if (currentParticipants.length >= _maxParticipants) {
        throw StateError(
          'This incident room has reached its participant limit.',
        );
      }
      participant = await RoomParticipant.db.insertRow(
        session,
        RoomParticipant(
          roomId: room.id!,
          userIdentifier: userId,
          displayName: name,
          joinedAt: now,
          lastSeenAt: now,
        ),
      );
    } else {
      await RoomParticipant.db.updateRow(
        session,
        participant.copyWith(displayName: name, lastSeenAt: now),
      );
    }

    if (isNewParticipant) {
      await _publish(
        session,
        room.id!,
        RoomActivity(
          kind: 'participant_joined',
          displayName: name,
          content: 'joined the incident room',
          createdAt: now,
        ),
      );
    }
    return _snapshot(session, room);
  }

  Future<RoomSnapshot> loadRoom(Session session, String joinCode) async {
    final room = await _findOpenRoom(session, joinCode);
    await _requireParticipant(session, room);
    return _snapshot(session, room);
  }

  Stream<RoomActivity> watchRoom(Session session, String joinCode) async* {
    final room = await _findOpenRoom(session, joinCode);
    await _requireParticipant(session, room);
    yield* session.messages.createStream<RoomActivity>(_channel(room.id!));
  }

  Future<RoomMessage> postMessage(
    Session session, {
    required String joinCode,
    required String content,
  }) async {
    final room = await _findOpenRoom(session, joinCode);
    final participant = await _requireParticipant(session, room);
    final text = content.trim();
    if (text.isEmpty || text.length > _maxMessageLength) {
      throw ArgumentError.value(
        content,
        'content',
        'Message must contain 1 to $_maxMessageLength characters.',
      );
    }

    final now = DateTime.now().toUtc();
    final message = await RoomMessage.db.insertRow(
      session,
      RoomMessage(
        roomId: room.id!,
        userIdentifier: participant.userIdentifier,
        authorName: participant.displayName,
        content: text,
        createdAt: now,
      ),
    );
    await RoomParticipant.db.updateRow(
      session,
      participant.copyWith(lastSeenAt: now),
    );
    await _publish(
      session,
      room.id!,
      RoomActivity(
        kind: 'message',
        displayName: participant.displayName,
        content: text,
        createdAt: now,
      ),
    );
    return message;
  }

  Future<void> closeRoom(Session session, String joinCode) async {
    final room = await _findOpenRoom(session, joinCode);
    if (room.createdByUserId != _userId(session)) {
      throw StateError('Only the room creator can close this room.');
    }
    await IncidentWarRoom.db.updateRow(
      session,
      room.copyWith(closedAt: DateTime.now().toUtc()),
    );
  }

  Future<RoomSnapshot> _snapshot(
    Session session,
    IncidentWarRoom room,
  ) async {
    final participants = await RoomParticipant.db.find(
      session,
      where: (t) => t.roomId.equals(room.id!),
      limit: _maxParticipants,
    );
    final messages = await RoomMessage.db.find(
      session,
      where: (t) => t.roomId.equals(room.id!),
      limit: 100,
    );
    messages.sort((a, b) => a.createdAt.compareTo(b.createdAt));
    return RoomSnapshot(
      room: room,
      participants: participants,
      messages: messages,
    );
  }

  Future<RoomParticipant> _requireParticipant(
    Session session,
    IncidentWarRoom room,
  ) async {
    final participant = await RoomParticipant.db.findFirstRow(
      session,
      where: (t) =>
          t.roomId.equals(room.id!) & t.userIdentifier.equals(_userId(session)),
    );
    if (participant == null) {
      throw StateError('Join this incident room before viewing or posting.');
    }
    return participant;
  }

  Future<IncidentWarRoom> _findOpenRoom(
    Session session,
    String joinCode,
  ) async {
    final code = joinCode.trim().toUpperCase();
    if (code.length != 10 || !RegExp(r'^[2-9A-HJ-NP-Z]+$').hasMatch(code)) {
      throw ArgumentError.value(joinCode, 'joinCode', 'Invalid room code.');
    }
    final room = await IncidentWarRoom.db.findFirstRow(
      session,
      where: (t) => t.joinCode.equals(code) & t.closedAt.equals(null),
    );
    if (room == null) throw StateError('Incident room not found or closed.');
    return room;
  }

  String _userId(Session session) {
    final userId = session.authenticated?.userIdentifier;
    if (userId == null || userId.isEmpty) {
      throw StateError('Sign in to use incident rooms.');
    }
    return userId;
  }

  String _validateDisplayName(String value) {
    final name = value.trim();
    if (name.isEmpty || name.length > 80) {
      throw ArgumentError.value(
        value,
        'displayName',
        'Use 1 to 80 characters.',
      );
    }
    return name;
  }

  String _newJoinCode() {
    final random = Random.secure();
    return List.generate(
      10,
      (_) => _codeAlphabet[random.nextInt(_codeAlphabet.length)],
    ).join();
  }

  String _channel(int roomId) => 'incident-room-$roomId';

  Future<void> _publish(
    Session session,
    int roomId,
    RoomActivity activity,
  ) async {
    await session.messages.postMessage(_channel(roomId), activity);
  }
}
