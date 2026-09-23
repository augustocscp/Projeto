import 'package:flutter/material.dart';

class LoginScreen extends StatelessWidget {
  final VoidCallback onLoginPressed;

  const LoginScreen({super.key, required this.onLoginPressed});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F2F8),
      body: Center(
        child: Container(
          width: 380,
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.08),
                blurRadius: 20,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.inventory_2_outlined,
                size: 56,
                color: Color(0xFF009CDF),
              ),
              const SizedBox(height: 16),
              const Text(
                'Sistema Patrimonial',
                style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text(
                'Urbi Mobilidade',
                style: TextStyle(color: Colors.grey),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: onLoginPressed,
                  icon: const Icon(Icons.login),
                  label: const Text('Entrar com Microsoft'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
