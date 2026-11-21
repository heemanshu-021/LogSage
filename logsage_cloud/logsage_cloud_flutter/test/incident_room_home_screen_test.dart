import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:logsage_cloud/screens/incident_room_home_screen.dart';

void main() {
  testWidgets('shows the incident-room create and join flows', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: IncidentRoomHomeScreen()),
    );

    expect(find.text('Respond together'), findsOneWidget);
    expect(find.text('Start an incident room'), findsOneWidget);
    expect(find.text('Create room'), findsOneWidget);
    expect(find.text('Join your team'), findsOneWidget);
    expect(find.text('Join room'), findsOneWidget);
  });
}
