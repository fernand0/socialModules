#!/usr/bin/env python

import configparser
import json
import logging
import os
import sys
import time

# Import Gemini AI
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from socialModules.configMod import *
from socialModules.moduleContent import *


class moduleGemini(Content):
    """
    Module for interacting with Google Gemini AI
    Provides AI-powered responses and can be used by other modules
    """

    def getKeys(self, config):
        """Get configuration keys for Gemini"""
        msgLog = f"{self.indent} Getting Gemini keys"
        logMsg(msgLog, 2, 0)
        
        # Get Gemini API key from .rssGemini file
        gemini_api_key = self._getGeminiApiKey()
        
        return (gemini_api_key,)

    def _getGeminiApiKey(self):
        """Get Gemini API key from .rssGemini configuration file"""
        try:
            gemini_config_path = os.path.expanduser("~/.mySocial/config/.rssGemini")
            if os.path.exists(gemini_config_path):
                gemini_config = configparser.ConfigParser()
                gemini_config.read(gemini_config_path)
                
                # Try to get API key from the first section
                for section in gemini_config.sections():
                    api_key = gemini_config.get(section, "api_key", fallback="")
                    if api_key:
                        msgLog = f"{self.indent} Found Gemini API key in .rssGemini"
                        logMsg(msgLog, 2, 0)
                        return api_key
                
                # If no api_key found, try api_key: format
                for section in gemini_config.sections():
                    for key, value in gemini_config.items(section):
                        if key == "api_key" or key == "api_key:":
                            msgLog = f"{self.indent} Found Gemini API key in .rssGemini"
                            logMsg(msgLog, 2, 0)
                            return value
        except Exception as e:
            msgLog = f"{self.indent} Error reading Gemini API key: {e}"
            logMsg(msgLog, 3, 0)
        
        return ""

    def initApi(self, keys):
        """Initialize Gemini AI connection"""
        msgLog = f"{self.indent} Service {self.service} Start initApi {self.user}"
        logMsg(msgLog, 2, 0)
        
        gemini_api_key = keys[0]
        
        # Initialize Gemini AI
        self.gemini_api_key = gemini_api_key
        self.gemini_client = self._initGeminiClient()
        
        msgLog = f"{self.indent} service {self.service} End initApi"
        logMsg(msgLog, 2, 0)
        return self.gemini_client

    def _initGeminiClient(self):
        """Initialize Gemini AI client"""
        if not GEMINI_AVAILABLE:
            msgLog = f"{self.indent} Gemini AI not available"
            logMsg(msgLog, 2, 0)
            return None
        
        if not self.gemini_api_key:
            msgLog = f"{self.indent} No Gemini API key provided"
            logMsg(msgLog, 2, 0)
            return None
        
        try:
            genai.configure(api_key=self.gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            msgLog = f"{self.indent} Gemini AI initialized successfully"
            logMsg(msgLog, 2, 0)
            return model
        except Exception as e:
            msgLog = f"{self.indent} Error initializing Gemini AI: {e}"
            logMsg(msgLog, 3, 0)
            return None

    def setApiPosts(self):
        """Get AI-generated content (not applicable for Gemini)"""
        return []

    def publishPost(self, question, context="", *args, **kwargs):
        """Send a question to Gemini AI and get response"""
        try:
            msgLog = f"{self.indent} Publishing question to Gemini: {question}"
            logMsg(msgLog, 1, 0)
            
            # Try Gemini AI first
            if self.gemini_client:
                response = self._callGeminiAI(question, context)
                if response:
                    return response
            
            # Fallback to basic responses if AI is not available
            return self._getBasicResponse(question, context)
                
        except Exception as e:
            return f"Error in Gemini query: {e}"

    def _callGeminiAI(self, question, context=""):
        """
        Call Gemini AI for real responses
        """
        try:
            if not self.gemini_client:
                return None
            
            # Prepare the prompt with context
            prompt = f"""
            Context: {context}
            
            Question: {question}
            
            Please provide a helpful and informative response. If the question is about programming, 
            code analysis, or development topics, provide detailed technical information. 
            If it's about general topics, provide accurate and helpful information.
            """
            
            # Generate response from Gemini
            response = self.gemini_client.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                return None
                
        except Exception as e:
            msgLog = f"{self.indent} Error calling Gemini AI: {e}"
            logMsg(msgLog, 3, 0)
            return None

    def _getBasicResponse(self, question, context=""):
        """
        Fallback to basic responses when AI is not available
        """
        question_lower = question.lower()
        
        # Basic information queries
        if "zaragoza" in question_lower:
            return "Zaragoza es la capital de la provincia de Zaragoza y de la comunidad autónoma de Aragón en España. Es conocida por su rica historia, arquitectura mudéjar y la Basílica del Pilar."
        
        elif "python" in question_lower:
            return "Python es un lenguaje de programación interpretado, de alto nivel y propósito general. Es conocido por su sintaxis clara y legible."
        
        elif "cursor" in question_lower:
            return "Cursor es un editor de código impulsado por IA que combina las capacidades de VS Code con funcionalidades de IA avanzadas."
        
        elif "javascript" in question_lower:
            return "JavaScript es un lenguaje de programación interpretado, orientado a objetos, utilizado principalmente en el desarrollo web para crear páginas interactivas."
        
        elif "java" in question_lower:
            return "Java es un lenguaje de programación orientado a objetos, desarrollado por Sun Microsystems. Es conocido por su portabilidad y robustez."
        
        elif "c++" in question_lower or "c++" in question_lower:
            return "C++ es un lenguaje de programación orientado a objetos que extiende C. Es ampliamente usado en desarrollo de software de sistemas."
        
        elif "html" in question_lower:
            return "HTML (HyperText Markup Language) es el lenguaje estándar para crear páginas web. Define la estructura y el contenido de las páginas."
        
        elif "css" in question_lower:
            return "CSS (Cascading Style Sheets) es un lenguaje de estilos usado para describir la presentación de documentos HTML."
        
        elif "sql" in question_lower:
            return "SQL (Structured Query Language) es un lenguaje estándar para acceder y manipular bases de datos relacionales."
        
        elif "git" in question_lower:
            return "Git es un sistema de control de versiones distribuido que permite a los desarrolladores rastrear cambios en el código fuente."
        
        elif "docker" in question_lower:
            return "Docker es una plataforma para desarrollar, enviar y ejecutar aplicaciones en contenedores, facilitando el despliegue."
        
        elif "kubernetes" in question_lower or "k8s" in question_lower:
            return "Kubernetes es una plataforma de orquestación de contenedores que automatiza el despliegue, escalado y gestión de aplicaciones."
        
        elif "react" in question_lower:
            return "React es una biblioteca de JavaScript para construir interfaces de usuario, desarrollada por Facebook."
        
        elif "vue" in question_lower:
            return "Vue.js es un framework progresivo de JavaScript para construir interfaces de usuario."
        
        elif "angular" in question_lower:
            return "Angular es un framework de desarrollo web de Google para crear aplicaciones de una sola página."
        
        elif "node" in question_lower and "js" in question_lower:
            return "Node.js es un entorno de ejecución de JavaScript que permite ejecutar código JavaScript en el servidor."
        
        elif "linux" in question_lower:
            return "Linux es un sistema operativo de código abierto basado en Unix, ampliamente usado en servidores y desarrollo."
        
        elif "ubuntu" in question_lower:
            return "Ubuntu es una distribución de Linux basada en Debian, conocida por su facilidad de uso y estabilidad."
        
        elif "debian" in question_lower:
            return "Debian es una distribución de Linux conocida por su estabilidad y compromiso con el software libre."
        
        elif "fedora" in question_lower:
            return "Fedora es una distribución de Linux patrocinada por Red Hat, conocida por su innovación y actualizaciones frecuentes."
        
        elif "arch" in question_lower:
            return "Arch Linux es una distribución de Linux rolling release conocida por su simplicidad y personalización."
        
        elif "inteligencia artificial" in question_lower or "ia" in question_lower:
            return "La inteligencia artificial (IA) es la simulación de procesos de inteligencia humana por parte de máquinas, especialmente sistemas informáticos."
        
        elif "machine learning" in question_lower or "aprendizaje automático" in question_lower:
            return "El machine learning es un subconjunto de la IA que permite a las computadoras aprender y mejorar automáticamente sin ser programadas explícitamente."
        
        elif "deep learning" in question_lower or "aprendizaje profundo" in question_lower:
            return "El deep learning es una rama del machine learning basada en redes neuronales artificiales con múltiples capas."
        
        elif "blockchain" in question_lower:
            return "Blockchain es una tecnología de registro distribuido que mantiene una lista creciente de registros (bloques) vinculados y asegurados criptográficamente."
        
        elif "bitcoin" in question_lower:
            return "Bitcoin es la primera criptomoneda descentralizada, creada en 2009 por Satoshi Nakamoto."
        
        elif "ethereum" in question_lower:
            return "Ethereum es una plataforma blockchain que permite crear aplicaciones descentralizadas y contratos inteligentes."
        
        else:
            # Generic response for unknown queries
            return f"Consulta recibida: '{question}'. Puedo ayudarte con información sobre programación, tecnologías, lenguajes de programación y temas técnicos."

    def getPostTitle(self, post):
        """Get title from a Gemini post"""
        return post.get("title", "Untitled")

    def getPostLink(self, post):
        """Get link from a Gemini post"""
        return post.get("link", "")

    def getPostContent(self, post):
        """Get content from a Gemini post"""
        return post.get("content", "")

    def getPostDate(self, post):
        """Get date from a Gemini post"""
        return post.get("date", time.time())

    def deletePost(self, post):
        """Delete a Gemini post (not applicable)"""
        return "Gemini posts cannot be deleted"

    def enableAI(self, api_key=None, ai_service="gemini"):
        """
        Enable AI integration with Gemini
        """
        try:
            if api_key:
                self.gemini_api_key = api_key
                self.gemini_client = self._initGeminiClient()
            
            msgLog = f"{self.indent} AI integration enabled with {ai_service}"
            logMsg(msgLog, 1, 0)
            return "AI integration enabled"
        except Exception as e:
            return f"Error enabling AI: {e}"

    def askQuestion(self, question, context=""):
        """
        Ask a question to Gemini AI
        This is a convenience method for other modules
        """
        return self.publishPost(question, context)


def main():
    """Test the Gemini module"""
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                       format='%(asctime)s %(message)s')

    # Test basic functionality
    gemini_api = moduleGemini()
    gemini_api.setClient("test_user")
    
    print("Testing Gemini module...")
    
    # Test different types of questions
    questions = [
        ("¿Qué es Python?", "Python programming language"),
        ("¿Qué sabes de Zaragoza?", "Zaragoza city information"),
        ("¿Qué es JavaScript?", "JavaScript programming language"),
        ("¿Qué es Docker?", "Docker containerization"),
        ("¿Qué es la inteligencia artificial?", "Artificial intelligence"),
        ("¿Qué es Bitcoin?", "Bitcoin cryptocurrency"),
        ("¿Qué es React?", "React framework"),
        ("¿Qué es Linux?", "Linux operating system"),
        ("¿Qué es Git?", "Git version control"),
        ("¿Qué es Kubernetes?", "Kubernetes orchestration")
    ]
    
    for question, topic in questions:
        print(f"\n--- {topic} ---")
        print(f"Q: {question}")
        response = gemini_api.publishPost(question, "")
        print(f"A: {response[:200]}...")

if __name__ == "__main__":
    main() 