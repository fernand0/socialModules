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
    Follows the same pattern as other modules in the project
    """

    def getKeys(self, config):
        """Get configuration keys for Gemini"""
        msgLog = f"{self.indent} Getting Gemini keys"
        logMsg(msgLog, 2, 0)
        
        # Read API key directly from config object
        api_key = config.get(self.user, "api_key", fallback="")
        
        return (api_key,)

    def initApi(self, keys):
        """Initialize Gemini AI connection"""
        msgLog = f"{self.indent} Service {self.service} Start initApi {self.user}"
        logMsg(msgLog, 2, 0)
        
        gemini_api_key = keys[0]
        
        # Initialize Gemini AI
        self.gemini_api_key = gemini_api_key
        self.gemini_client = None
        
        # Set up URL for consistency with other modules
        self.url = "https://generativeai.google.com"
        
        # Initialize Gemini client if API key is available
        if not GEMINI_AVAILABLE:
            msgLog = f"{self.indent} Gemini AI not available"
            logMsg(msgLog, 2, 0)
        elif not self.gemini_api_key:
            msgLog = f"{self.indent} No Gemini API key provided"
            logMsg(msgLog, 2, 0)
        else:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-1.5-pro')
                msgLog = f"{self.indent} Gemini AI initialized successfully"
                logMsg(msgLog, 2, 0)
            except Exception as e:
                msgLog = f"{self.indent} Error initializing Gemini AI: {e}"
                logMsg(msgLog, 3, 0)
        
        msgLog = f"{self.indent} service {self.service} End initApi"
        logMsg(msgLog, 2, 0)
        return self.gemini_client

    def setApiPosts(self):
        """Get AI-generated content (not applicable for Gemini, returns empty list)"""
        # Gemini doesn't have posts like social networks, so return empty list
        return []

    def setPostsType(self, postsType="question"):
        """Set the type of posts for Gemini (default: question)"""
        self.postsType = postsType

    def publishApiPost(self, *args, **kwargs):
        """Send a question to Gemini AI and get response"""
        try:
            # Extract question and context from args/kwargs
            question = args[0] if args else kwargs.get('question', '')
            context = args[1] if len(args) > 1 else kwargs.get('context', '')
            
            msgLog = f"{self.indent} Publishing question to Gemini: {question}"
            logMsg(msgLog, 1, 0)
            
            # Try Gemini AI
            if self.gemini_client:
                response = self._callGeminiAI(question, context)
                if response:
                    return response
            
            # If no AI available, return error message
            return "Error: Gemini AI not available or no API key configured"
                
        except Exception as e:
            return f"Error in Gemini query: {e}"

    def publishApiQuestion(self, *args, **kwargs):
        """Alias for publishApiPost for clarity"""
        return self.publishApiPost(*args, **kwargs)

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
                # Initialize Gemini client directly
                if GEMINI_AVAILABLE and self.gemini_api_key:
                    try:
                        genai.configure(api_key=self.gemini_api_key)
                        self.gemini_client = genai.GenerativeModel('gemini-1.5-pro')
                    except Exception as e:
                        msgLog = f"{self.indent} Error initializing Gemini AI: {e}"
                        logMsg(msgLog, 3, 0)
                        self.gemini_client = None
            
            msgLog = f"{self.indent} AI integration enabled with {ai_service}"
            logMsg(msgLog, 1, 0)
            return "AI integration enabled"
        except Exception as e:
            return f"Error enabling AI: {e}"

    def askQuestion(self, *args, **kwargs):
        """
        Ask a question to Gemini AI
        This is a convenience method for other modules
        """
        return self.publishApiPost(*args, **kwargs)


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
        response = gemini_api.publishApiPost(question, "")
        print(f"A: {response[:200]}...")

if __name__ == "__main__":
    main() 