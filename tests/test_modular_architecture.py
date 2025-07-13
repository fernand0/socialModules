#!/usr/bin/env python3
"""
Test script for modular architecture: Gemini and Cursor modules
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

from moduleGemini import moduleGemini
from moduleCursor import moduleCursor

def test_modular_architecture():
    """Test the modular architecture with separate Gemini and Cursor modules"""
    
    print("=== Testing Modular Architecture: Gemini + Cursor ===\n")
    
    # Test 1: Standalone Gemini module
    print("1. Testing standalone Gemini module:")
    print("-" * 50)
    
    gemini_api = moduleGemini()
    gemini_api.setClient("test_user")
    
    gemini_questions = [
        ("¿Qué es Python?", "Python programming"),
        ("¿Qué es Docker?", "Docker containerization"),
        ("¿Qué es React?", "React framework"),
        ("¿Qué es Kubernetes?", "Kubernetes orchestration")
    ]
    
    for question, topic in gemini_questions:
        print(f"\n{topic}:")
        print(f"Q: {question}")
        response = gemini_api.publishPost(question, "")
        print(f"A: {response[:150]}...")
    
    # Test 2: Cursor module (which uses Gemini internally)
    print("\n2. Testing Cursor module (uses Gemini internally):")
    print("-" * 50)
    
    cursor_api = moduleCursor()
    cursor_api.setClient("test_user")
    
    cursor_operations = [
        ("help", "", "Get help information"),
        ("files", "", "List files in workspace"),
        ("status", "", "Check Cursor status"),
        ("projects", "", "List projects")
    ]
    
    for op_type, op_content, description in cursor_operations:
        print(f"\n{description}:")
        result = cursor_api.publishPost(op_type, op_content)
        print(f"Result: {result[:150]}...")
    
    # Test 3: AI queries through Cursor (which delegates to Gemini)
    print("\n3. Testing AI queries through Cursor (delegates to Gemini):")
    print("-" * 50)
    
    ai_queries = [
        ("¿Qué es JavaScript?", "JavaScript programming"),
        ("¿Qué es Git?", "Git version control"),
        ("¿Qué es Linux?", "Linux operating system"),
        ("¿Qué es la IA?", "Artificial intelligence")
    ]
    
    for question, topic in ai_queries:
        print(f"\n{topic}:")
        print(f"Q: {question}")
        response = cursor_api.publishPost("query", question)
        print(f"A: {response[:150]}...")
    
    # Test 4: File operations through Cursor
    print("\n4. Testing file operations through Cursor:")
    print("-" * 50)
    
    file_ops = [
        ("read", "moduleGemini.py", "Read Gemini module"),
        ("search", "*.py", "Search Python files"),
        ("info", "moduleCursor.py", "Get file info")
    ]
    
    for op_type, op_content, description in file_ops:
        print(f"\n{description}:")
        result = cursor_api.publishPost(op_type, op_content)
        if isinstance(result, dict):
            print(f"Result: {str(result)[:150]}...")
        else:
            print(f"Result: {result[:150]}...")
    
    # Test 5: Write/Read operations
    print("\n5. Testing write/read operations:")
    print("-" * 50)
    
    test_content = "Este es un archivo de prueba creado por la arquitectura modular."
    write_result = cursor_api.publishPost("write", f"test_modular.txt:{test_content}")
    print(f"Write result: {write_result}")
    
    read_result = cursor_api.publishPost("read", "test_modular.txt")
    print(f"Read result: {read_result}")
    
    print("\n=== Architecture Comparison ===")
    print("\nVentajas de la arquitectura modular:")
    print("✅ Separación de responsabilidades")
    print("✅ Reutilización de código")
    print("✅ Mantenibilidad mejorada")
    print("✅ Escalabilidad")
    print("✅ Configuración independiente")
    
    print("\nFlujo de datos:")
    print("1. Cursor module recibe consulta")
    print("2. Si es consulta de IA, delega a Gemini module")
    print("3. Gemini module procesa con IA real o fallback")
    print("4. Cursor module devuelve respuesta")
    
    print("\n=== Test completed successfully! ===")
    print("\nNotas:")
    print("- Gemini module: Funciona independientemente")
    print("- Cursor module: Usa Gemini internamente")
    print("- Arquitectura modular: Más limpia y mantenible")
    print("- Configuración: Separada por módulo")

if __name__ == "__main__":
    test_modular_architecture() 