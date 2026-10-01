import 'package:flutter_test/flutter_test.dart';
import 'package:sistema_patrimonial/main.dart';

void main() {
  testWidgets('O aplicativo inicia corretamente', (tester) async {
    await tester.pumpWidget(const PatrimonioApp());

    expect(find.byType(PatrimonioApp), findsOneWidget);
  });
}
