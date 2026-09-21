import 'package:http/http.dart' as http;

import 'http_client_default.dart'
    if (dart.library.js_interop) 'http_client_web.dart';

http.Client createHttpClient() => createPlatformHttpClient();
