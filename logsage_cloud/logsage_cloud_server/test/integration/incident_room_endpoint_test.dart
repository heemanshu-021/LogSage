import 'package:test/test.dart';

import 'test_tools/serverpod_test_tools.dart';

void main() {
  withServerpod('Given an incident room', (sessionBuilder, endpoints) {
    final owner = sessionBuilder.copyWith(
      authentication: AuthenticationOverride.authenticationInfo(
        'responder-owner',
        {},
      ),
    );
    final teammate = sessionBuilder.copyWith(
      authentication: AuthenticationOverride.authenticationInfo(
        'responder-teammate',
        {},
      ),
    );

    test(
      'shares persisted messages and live updates with joined responders',
      () async {
        final room = await endpoints.incidentRoom.createRoom(
          owner,
          incidentId: 'INC-42',
          incidentTitle: 'NameNode heartbeat delayed',
          displayName: 'Asha',
        );

        final snapshot = await endpoints.incidentRoom.joinRoom(
          teammate,
          joinCode: room.joinCode,
          displayName: 'Ravi',
        );
        expect(
          snapshot.participants.map((person) => person.displayName),
          containsAll(['Asha', 'Ravi']),
        );

        final nextActivity = endpoints.incidentRoom
            .watchRoom(owner, room.joinCode)
            .first
            .timeout(const Duration(seconds: 5));
        // The test client starts the remote stream on subscription. Give that
        // subscription a turn to reach Serverpod before publishing the event.
        await Future<void>.delayed(const Duration(milliseconds: 100));

        final message = await endpoints.incidentRoom.postMessage(
          teammate,
          joinCode: room.joinCode,
          content: 'Checking the NameNode heartbeat on worker-03.',
        );
        expect(message.authorName, 'Ravi');

        final activity = await nextActivity;
        expect(activity.kind, 'message');
        expect(activity.displayName, 'Ravi');
        expect(activity.content, message.content);

        final refreshed = await endpoints.incidentRoom.loadRoom(
          owner,
          room.joinCode,
        );
        expect(refreshed.messages, hasLength(1));
        expect(refreshed.messages.single.content, message.content);
        expect(refreshed.room.incidentId, 'INC-42');
      },
    );

    test('rejects a responder who has not joined the room', () async {
      final room = await endpoints.incidentRoom.createRoom(
        owner,
        incidentId: 'INC-43',
        incidentTitle: 'DataNode disk alert',
        displayName: 'Asha',
      );
      final stranger = sessionBuilder.copyWith(
        authentication: AuthenticationOverride.authenticationInfo(
          'responder-stranger',
          {},
        ),
      );

      await expectLater(
        endpoints.incidentRoom.postMessage(
          stranger,
          joinCode: room.joinCode,
          content: 'This must not be accepted.',
        ),
        throwsA(isA<StateError>()),
      );
    });
  }, rollbackDatabase: RollbackDatabase.disabled);
}
