#!/usr/bin/env python

import configparser
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from socialModules.configMod import *
from socialModules.moduleContent import *


class moduleCursor(Content):
    """
    Module for interacting with Cursor IDE
    Allows querying Cursor, managing projects, and automating development tasks
    Uses Gemini AI for intelligent responses
    """

    def getKeys(self, config):
        """Get configuration keys for Cursor"""
        msgLog = f"{self.indent} Getting Cursor keys"
        logMsg(msgLog, 2, 0)
        
        # Get Cursor installation path
        cursor_path = config.get(self.user, "cursor_path", fallback="")
        api_key = config.get(self.user, "api_key", fallback="")
        workspace_path = config.get(self.user, "workspace_path", fallback="")
        
        return (cursor_path, api_key, workspace_path)

    def initApi(self, keys):
        """Initialize Cursor API connection"""
        msgLog = f"{self.indent} Service {self.service} Start initApi {self.user}"
        logMsg(msgLog, 2, 0)
        
        cursor_path, api_key, workspace_path = keys
        
        # Set up Cursor paths
        self.cursor_path = cursor_path or self._findCursorPath()
        self.api_key = api_key
        self.workspace_path = workspace_path or os.getcwd()
        
        # Initialize Gemini AI module for AI responses
        self.gemini_module = self._initGeminiModule()
        
        # Initialize client (could be a subprocess or API client)
        client = self._initCursorClient()
        
        msgLog = f"{self.indent} service {self.service} End initApi"
        logMsg(msgLog, 2, 0)
        return client

    def _findCursorPath(self):
        """Find Cursor installation path"""
        possible_paths = [
            "/usr/bin/cursor",
            "/usr/local/bin/cursor",
            "/opt/cursor/cursor",
            os.path.expanduser("~/.local/bin/cursor"),
            os.path.expanduser("~/Applications/Cursor.app/Contents/MacOS/Cursor"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Try to find in PATH
        try:
            result = subprocess.run(["which", "cursor"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return "cursor"  # Assume it's in PATH

    def _initCursorClient(self):
        """Initialize Cursor client"""
        # For now, we'll use subprocess to interact with Cursor
        # In the future, this could be replaced with a proper API client
        return {
            "cursor_path": self.cursor_path,
            "workspace_path": self.workspace_path,
            "api_key": self.api_key
        }

    def _initGeminiModule(self):
        """Initialize Gemini module for AI responses"""
        try:
            # Import and initialize Gemini module
            from moduleGemini import moduleGemini
            gemini_module = moduleGemini()
            gemini_module.setClient("gemini_user")
            msgLog = f"{self.indent} Gemini module initialized successfully"
            logMsg(msgLog, 2, 0)
            return gemini_module
        except Exception as e:
            msgLog = f"{self.indent} Error initializing Gemini module: {e}"
            logMsg(msgLog, 3, 0)
            return None

    def setApiPosts(self):
        """Get recent files/projects from Cursor"""
        posts = []
        try:
            # Get recent files from Cursor workspace
            workspace_files = self._getWorkspaceFiles()
            for file_path in workspace_files:
                post = {
                    "title": os.path.basename(file_path),
                    "link": file_path,
                    "content": self._readFileContent(file_path),
                    "date": time.time()
                }
                posts.append(post)
        except Exception as e:
            msgLog = f"{self.indent} Error getting Cursor posts: {e}"
            logMsg(msgLog, 3, 0)
        
        return posts

    def _getWorkspaceFiles(self):
        """Get list of files in current workspace"""
        files = []
        try:
            for root, dirs, filenames in os.walk(self.workspace_path):
                for filename in filenames:
                    if not filename.startswith('.'):
                        file_path = os.path.join(root, filename)
                        files.append(file_path)
        except Exception as e:
            msgLog = f"{self.indent} Error walking workspace: {e}"
            logMsg(msgLog, 3, 0)
        
        return files[:50]  # Limit to 50 files

    def _readFileContent(self, file_path):
        """Read content of a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()[:1000]  # Limit to first 1000 chars
        except:
            return ""

    def queryCursor(self, query, context=""):
        """
        Send a query to Cursor and get response
        This could be implemented using Cursor's API or CLI
        """
        msgLog = f"{self.indent} Querying Cursor: {query}"
        logMsg(msgLog, 1, 0)
        
        try:
            # For now, we'll simulate a response
            # In a real implementation, this would call Cursor's API
            response = self._simulateCursorQuery(query, context)
            return response
        except Exception as e:
            msgLog = f"{self.indent} Error querying Cursor: {e}"
            logMsg(msgLog, 3, 0)
            return f"Error: {e}"

    def _simulateCursorQuery(self, query, context=""):
        """Execute Cursor-related operations without opening GUI"""
        try:
            if "help" in query.lower():
                return "Cursor is an AI-powered code editor. Available commands: files, status, projects, analyze"
            
            elif "version" in query.lower():
                # Try to get version without opening GUI
                try:
                    result = subprocess.run([self.cursor_path, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return result.stdout
                    else:
                        return "Cursor version information (GUI not opened)"
                except:
                    return "Cursor version information (GUI not opened)"
            
            elif "files" in query.lower():
                files = self._getWorkspaceFiles()
                return f"Found {len(files)} files in workspace: {', '.join([os.path.basename(f) for f in files[:10]])}"
            
            elif "status" in query.lower():
                # Check if Cursor is running without opening GUI
                try:
                    result = subprocess.run(["pgrep", "-f", "cursor"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return "Cursor is running"
                    else:
                        return "Cursor is not running"
                except:
                    return "Cursor status: Unknown"
            
            elif "projects" in query.lower():
                projects = self.listProjects()
                if isinstance(projects, list):
                    return f"Projects in workspace: {', '.join(projects)}"
                else:
                    return projects
            
            elif "analyze" in query.lower():
                # Analyze current workspace
                files = self._getWorkspaceFiles()
                python_files = [f for f in files if f.endswith('.py')]
                return f"Workspace analysis: {len(files)} total files, {len(python_files)} Python files"
            
            else:
                # For other queries, provide helpful information without opening GUI
                return f"Query '{query}' received. Available operations: files, projects, analyze, status"
                
        except Exception as e:
            return f"Error executing Cursor operation: {e}"

    def openFile(self, file_path):
        """Open a file in Cursor (without GUI)"""
        try:
            full_path = os.path.abspath(file_path)
            if os.path.exists(full_path):
                # Just return success without opening GUI
                return f"File ready: {full_path}"
            else:
                return f"File not found: {full_path}"
        except Exception as e:
            return f"Error with file: {e}"

    def createProject(self, project_name, project_type="python"):
        """Create a new project in Cursor workspace (without opening GUI)"""
        try:
            project_path = os.path.join(self.workspace_path, project_name)
            os.makedirs(project_path, exist_ok=True)
            
            # Create basic project structure
            if project_type == "python":
                self._createPythonProject(project_path)
            elif project_type == "javascript":
                self._createJavaScriptProject(project_path)
            
            # Don't open project in Cursor GUI
            return f"Created {project_type} project: {project_path}"
        except Exception as e:
            return f"Error creating project: {e}"

    def readFile(self, file_path):
        """Read content of a file without opening Cursor"""
        try:
            full_path = os.path.abspath(file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return f"File not found: {full_path}"
        except Exception as e:
            return f"Error reading file: {e}"

    def writeFile(self, file_path, content):
        """Write content to a file without opening Cursor"""
        try:
            full_path = os.path.abspath(file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"File written: {full_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def searchFiles(self, pattern, file_type=None):
        """Search for files in workspace without opening Cursor"""
        import glob
        import fnmatch
        
        try:
            search_pattern = os.path.join(self.workspace_path, "**", pattern)
            files = glob.glob(search_pattern, recursive=True)
            
            if file_type:
                files = [f for f in files if fnmatch.fnmatch(f, f"*.{file_type}")]
            
            return files
        except Exception as e:
            return f"Error searching files: {e}"

    def getFileInfo(self, file_path):
        """Get information about a file without opening Cursor"""
        try:
            full_path = os.path.abspath(file_path)
            if os.path.exists(full_path):
                stat = os.stat(full_path)
                return {
                    "path": full_path,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "created": stat.st_ctime,
                    "extension": os.path.splitext(full_path)[1],
                    "basename": os.path.basename(full_path)
                }
            else:
                return f"File not found: {full_path}"
        except Exception as e:
            return f"Error getting file info: {e}"

    def listProjects(self):
        """List all projects in workspace without opening Cursor"""
        try:
            projects = []
            for item in os.listdir(self.workspace_path):
                item_path = os.path.join(self.workspace_path, item)
                if os.path.isdir(item_path):
                    # Check if it looks like a project
                    project_files = ["package.json", "requirements.txt", "setup.py", 
                                   "Cargo.toml", "pom.xml", "build.gradle"]
                    for project_file in project_files:
                        if os.path.exists(os.path.join(item_path, project_file)):
                            projects.append(item)
                            break
            return projects
        except Exception as e:
            return f"Error listing projects: {e}"

    def analyzeCode(self, file_path):
        """Analyze code file without opening Cursor"""
        try:
            content = self.readFile(file_path)
            if isinstance(content, str):
                # Basic code analysis
                lines = content.split('\n')
                analysis = {
                    "file": file_path,
                    "lines": len(lines),
                    "characters": len(content),
                    "empty_lines": len([l for l in lines if l.strip() == '']),
                    "comment_lines": len([l for l in lines if l.strip().startswith('#')]),
                    "imports": len([l for l in lines if l.strip().startswith('import') or l.strip().startswith('from')])
                }
                return analysis
            else:
                return content  # Error message
        except Exception as e:
            return f"Error analyzing code: {e}"

    def _createPythonProject(self, project_path):
        """Create basic Python project structure"""
        files = {
            "main.py": "# Main application file\n\nif __name__ == '__main__':\n    print('Hello from Cursor!')\n",
            "requirements.txt": "# Python dependencies\n",
            "README.md": f"# {os.path.basename(project_path)}\n\nProject created with Cursor.\n",
            ".gitignore": "*.pyc\n__pycache__/\n.env\n"
        }
        
        for filename, content in files.items():
            file_path = os.path.join(project_path, filename)
            with open(file_path, 'w') as f:
                f.write(content)

    def _createJavaScriptProject(self, project_path):
        """Create basic JavaScript project structure"""
        files = {
            "index.js": "// Main application file\n\nconsole.log('Hello from Cursor!');\n",
            "package.json": '{\n  "name": "cursor-project",\n  "version": "1.0.0",\n  "description": "Project created with Cursor"\n}\n',
            "README.md": f"# {os.path.basename(project_path)}\n\nProject created with Cursor.\n"
        }
        
        for filename, content in files.items():
            file_path = os.path.join(project_path, filename)
            with open(file_path, 'w') as f:
                f.write(content)

    def getPostTitle(self, post):
        """Get title from a Cursor post (file)"""
        return post.get("title", "Untitled")

    def getPostLink(self, post):
        """Get link from a Cursor post (file path)"""
        return post.get("link", "")

    def getPostContent(self, post):
        """Get content from a Cursor post (file content)"""
        return post.get("content", "")

    def getPostDate(self, post):
        """Get date from a Cursor post"""
        return post.get("date", time.time())

    def queryGenericInfo(self, question, context=""):
        """
        Make generic information queries to Cursor
        This could integrate with Cursor's AI features or provide helpful responses
        """
        try:
            # Try to use real AI services if available
            ai_response = self._getAIResponse(question, context)
            if ai_response:
                return ai_response
            
            # Fallback to basic responses if AI is not available
            question_lower = question.lower()
            
            # Basic information queries
            if "zaragoza" in question_lower:
                return "Zaragoza es la capital de la provincia de Zaragoza y de la comunidad autónoma de Aragón en España. Es conocida por su rica historia, arquitectura mudéjar y la Basílica del Pilar."
            
            elif "python" in question_lower:
                return "Python es un lenguaje de programación interpretado, de alto nivel y propósito general. Es conocido por su sintaxis clara y legible."
            
            elif "cursor" in question_lower:
                return "Cursor es un editor de código impulsado por IA que combina las capacidades de VS Code con funcionalidades de IA avanzadas."
            
            elif "workspace" in question_lower or "proyecto" in question_lower:
                files = self._getWorkspaceFiles()
                return f"El workspace actual contiene {len(files)} archivos. Proyectos detectados: {', '.join(self.listProjects())}"
            
            elif "archivos" in question_lower or "files" in question_lower:
                files = self._getWorkspaceFiles()
                return f"Hay {len(files)} archivos en el workspace. Tipos principales: {self._getFileTypes(files)}"
            
            elif "código" in question_lower or "code" in question_lower:
                python_files = self.searchFiles("*.py")
                return f"Encontrados {len(python_files)} archivos Python en el workspace."
            
            elif "ayuda" in question_lower or "help" in question_lower:
                return "Puedo ayudarte con: información sobre archivos, análisis de código, gestión de proyectos, y consultas sobre el workspace."
            
            else:
                # Generic response for unknown queries
                return f"Consulta recibida: '{question}'. Puedo ayudarte con información sobre archivos, proyectos, código y el workspace de Cursor."
                
        except Exception as e:
            return f"Error en consulta genérica: {e}"

    def _getAIResponse(self, question, context=""):
        """
        Get response from Gemini AI module
        """
        try:
            # Try Gemini AI first
            if self.gemini_module:
                return self.gemini_module.publishPost(question, context)
            
            # Fallback to basic responses if AI is not available
            return self._getBasicResponse(question, context)
            
        except Exception as e:
            msgLog = f"{self.indent} Error getting AI response: {e}"
            logMsg(msgLog, 3, 0)
            return self._getBasicResponse(question, context)

    def _callGeminiAI(self, question, context=""):
        """
        Call Gemini AI for real responses (delegated to Gemini module)
        """
        try:
            if self.gemini_module:
                return self.gemini_module.publishPost(question, context)
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
        
        elif "workspace" in question_lower or "proyecto" in question_lower:
            files = self._getWorkspaceFiles()
            return f"El workspace actual contiene {len(files)} archivos. Proyectos detectados: {', '.join(self.listProjects())}"
        
        elif "archivos" in question_lower or "files" in question_lower:
            files = self._getWorkspaceFiles()
            return f"Hay {len(files)} archivos en el workspace. Tipos principales: {self._getFileTypes(files)}"
        
        elif "código" in question_lower or "code" in question_lower:
            python_files = self.searchFiles("*.py")
            return f"Encontrados {len(python_files)} archivos Python en el workspace."
        
        elif "ayuda" in question_lower or "help" in question_lower:
            return "Puedo ayudarte con: información sobre archivos, análisis de código, gestión de proyectos, y consultas sobre el workspace."
        
        else:
            # Generic response for unknown queries
            return f"Consulta recibida: '{question}'. Puedo ayudarte con información sobre archivos, proyectos, código y el workspace de Cursor."

    def enableAI(self, api_key=None, ai_service="gemini"):
        """
        Enable AI integration with Gemini
        """
        try:
            if api_key:
                # This method is no longer needed as Gemini is integrated
                # self.gemini_api_key = api_key
                # self.gemini_client = self._initGeminiClient()
                pass # No-op as Gemini is now a module
            
            msgLog = f"{self.indent} AI integration enabled with {ai_service}"
            logMsg(msgLog, 1, 0)
            return "AI integration enabled"
        except Exception as e:
            return f"Error enabling AI: {e}"

    def _getFileTypes(self, files):
        """Get file type statistics"""
        extensions = {}
        for file in files:
            ext = os.path.splitext(file)[1]
            extensions[ext] = extensions.get(ext, 0) + 1
        
        # Return top 5 file types
        sorted_types = sorted(extensions.items(), key=lambda x: x[1], reverse=True)
        return ", ".join([f"{ext}({count})" for ext, count in sorted_types[:5]])

    def publishPost(self, title, content, *args, **kwargs):
        """Send a query to Cursor and get response"""
        try:
            # title acts as query type, content as the specific query
            query_type = title.lower()
            query_content = content
            
            msgLog = f"{self.indent} Publishing query to Cursor: {query_type} - {query_content}"
            logMsg(msgLog, 1, 0)
            
            if query_type == "help":
                return self.queryCursor("help")
            
            elif query_type == "files":
                return self.queryCursor("files")
            
            elif query_type == "status":
                return self.queryCursor("status")
            
            elif query_type == "projects":
                return self.queryCursor("projects")
            
            elif query_type == "analyze":
                return self.queryCursor("analyze")
            
            elif query_type == "read":
                # Read a specific file
                if query_content:
                    return self.readFile(query_content)
                else:
                    return "Error: No file specified for read operation"
            
            elif query_type == "write":
                # Write content to a file
                if ":" in query_content:
                    file_path, content_to_write = query_content.split(":", 1)
                    return self.writeFile(file_path.strip(), content_to_write.strip())
                else:
                    return "Error: Use format 'filepath:content' for write operation"
            
            elif query_type == "search":
                # Search for files
                if query_content:
                    return str(self.searchFiles(query_content))
                else:
                    return str(self.searchFiles("*"))
            
            elif query_type == "info":
                # Get file information
                if query_content:
                    return str(self.getFileInfo(query_content))
                else:
                    return "Error: No file specified for info operation"
            
            elif query_type == "analyze_code":
                # Analyze specific code file
                if query_content:
                    return str(self.analyzeCode(query_content))
                else:
                    return "Error: No file specified for code analysis"
            
            elif query_type == "create_project":
                # Create a new project
                if ":" in query_content:
                    project_name, project_type = query_content.split(":", 1)
                    return self.createProject(project_name.strip(), project_type.strip())
                else:
                    return self.createProject(query_content, "python")
            
            elif query_type == "list_projects":
                return str(self.listProjects())
            
            elif query_type == "custom":
                # Custom query to Cursor
                return self.queryCursor(query_content)
            
            elif query_type == "query" or query_type == "pregunta":
                # Generic information query
                return self.queryGenericInfo(query_content)
            
            else:
                # Default: treat as generic query
                return self.queryGenericInfo(f"{title}: {content}")
                
        except Exception as e:
            return f"Error in Cursor query: {e}"

    def deletePost(self, post):
        """Delete a file from Cursor workspace"""
        try:
            file_path = self.getPostLink(post)
            if os.path.exists(file_path):
                os.remove(file_path)
                return f"Deleted file: {file_path}"
            else:
                return f"File not found: {file_path}"
        except Exception as e:
            return f"Error deleting file: {e}"


def main():
    """Test the Cursor module"""
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                       format='%(asctime)s %(message)s')

    # Test basic functionality
    cursor_api = moduleCursor()
    cursor_api.setClient("test_user")
    
    print("Testing Cursor module with publish queries...")
    
    # Test different types of queries using publishPost
    queries = [
        ("help", "", "Get help information"),
        ("files", "", "List files in workspace"),
        ("status", "", "Check Cursor status"),
        ("projects", "", "List projects"),
        ("analyze", "", "Analyze workspace"),
        ("read", "moduleCursor.py", "Read a file"),
        ("search", "*.py", "Search for Python files"),
        ("info", "moduleCursor.py", "Get file info"),
        ("analyze_code", "moduleCursor.py", "Analyze code file"),
        ("create_project", "test_publish_project:python", "Create a project"),
        ("list_projects", "", "List all projects"),
        ("custom", "files", "Custom query")
    ]
    
    for query_type, query_content, description in queries:
        print(f"\n--- Testing: {description} ---")
        result = cursor_api.publishPost(query_type, query_content)
        print(f"Result: {result[:200]}...")  # Show first 200 chars
    
    print("\n--- Testing write operation ---")
    result = cursor_api.publishPost("write", "test_file.txt:Hello from Cursor module!")
    print(f"Write result: {result}")
    
    print("\n--- Testing read of written file ---")
    result = cursor_api.publishPost("read", "test_file.txt")
    print(f"Read result: {result}")
    
    print("\n--- Testing generic information queries ---")
    generic_queries = [
        ("query", "¿Qué sabes de Zaragoza?", "Zaragoza info"),
        ("pregunta", "¿Qué es Python?", "Python info"),
        ("query", "¿Qué es Cursor?", "Cursor info"),
        ("query", "¿Qué hay en el workspace?", "Workspace info"),
        ("query", "¿Cuántos archivos hay?", "Files count"),
        ("query", "¿Qué tipos de código hay?", "Code types"),
        ("query", "¿Puedes ayudarme?", "Help request"),
        ("query", "¿Qué es JavaScript?", "Unknown topic")
    ]
    
    for query_type, question, description in generic_queries:
        print(f"\n--- {description} ---")
        result = cursor_api.publishPost(query_type, question)
        print(f"Q: {question}")
        print(f"A: {result}")

if __name__ == "__main__":
    main() 
