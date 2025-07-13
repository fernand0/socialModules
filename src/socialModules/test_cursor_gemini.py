#!/usr/bin/env python3
"""
Test script for Cursor module with Gemini AI integration
"""

import sys
import os

# Add current directory to path
sys.path.append('.')

from moduleCursor import moduleCursor

def test_cursor_module():
    """Test the Cursor module with various queries"""
    
    print("=== Testing Cursor Module with Gemini AI Integration ===\n")
    
    # Initialize the module
    cursor_api = moduleCursor()
    cursor_api.setClient('test_user')
    
    print("1. Testing basic Cursor operations:")
    print("-" * 50)
    
    # Test basic operations
    operations = [
        ("help", "", "Get help information"),
        ("files", "", "List files in workspace"),
        ("status", "", "Check Cursor status"),
        ("projects", "", "List projects"),
        ("analyze", "", "Analyze workspace")
    ]
    
    for op_type, op_content, description in operations:
        print(f"\n{description}:")
        result = cursor_api.publishPost(op_type, op_content)
        print(f"Result: {result[:150]}...")
    
    print("\n2. Testing file operations:")
    print("-" * 50)
    
    # Test file operations
    file_ops = [
        ("read", "moduleCursor.py", "Read a file"),
        ("search", "*.py", "Search for Python files"),
        ("info", "moduleCursor.py", "Get file info"),
        ("analyze_code", "moduleCursor.py", "Analyze code file")
    ]
    
    for op_type, op_content, description in file_ops:
        print(f"\n{description}:")
        result = cursor_api.publishPost(op_type, op_content)
        if isinstance(result, dict):
            print(f"Result: {str(result)[:150]}...")
        else:
            print(f"Result: {result[:150]}...")
    
    print("\n3. Testing project operations:")
    print("-" * 50)
    
    # Test project operations
    project_ops = [
        ("create_project", "test_gemini_project:python", "Create a Python project"),
        ("list_projects", "", "List all projects")
    ]
    
    for op_type, op_content, description in project_ops:
        print(f"\n{description}:")
        result = cursor_api.publishPost(op_type, op_content)
        print(f"Result: {result}")
    
    print("\n4. Testing Gemini AI queries:")
    print("-" * 50)
    
    # Test Gemini AI queries
    ai_queries = [
        ("¿Qué es Python?", "Python programming language"),
        ("¿Qué sabes de Zaragoza?", "Zaragoza city information"),
        ("¿Qué es JavaScript?", "JavaScript programming language"),
        ("¿Cómo optimizar código Python?", "Python optimization"),
        ("¿Qué patrones de diseño existen?", "Design patterns"),
        ("¿Qué es la inteligencia artificial?", "Artificial intelligence")
    ]
    
    for question, topic in ai_queries:
        print(f"\n{topic}:")
        print(f"Q: {question}")
        response = cursor_api.publishPost("query", question)
        print(f"A: {response[:200]}...")
    
    print("\n5. Testing write/read operations:")
    print("-" * 50)
    
    # Test write and read
    test_content = "Este es un archivo de prueba creado por el módulo Cursor con integración Gemini AI."
    write_result = cursor_api.publishPost("write", f"test_gemini.txt:{test_content}")
    print(f"Write result: {write_result}")
    
    read_result = cursor_api.publishPost("read", "test_gemini.txt")
    print(f"Read result: {read_result}")
    
    print("\n=== Test completed successfully! ===")
    print("\nNotas:")
    print("- Si ves respuestas básicas, es porque Gemini no está disponible o hay errores de cuota")
    print("- Si ves respuestas detalladas de IA, significa que Gemini está funcionando correctamente")
    print("- El módulo siempre funciona, incluso sin Gemini, usando respuestas de fallback")

if __name__ == "__main__":
    test_cursor_module() 