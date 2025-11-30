"""
System Executor - Infrastructure Installation and Management
Handles system-level operations like installing Kubernetes, Docker, etc.
"""
import logging
import subprocess
import platform
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SystemExecutor:
    """Execute system-level commands for infrastructure setup"""
    
    def __init__(self):
        self.os_type = platform.system().lower()
        self.is_windows = self.os_type == 'windows'
        self.is_linux = self.os_type == 'linux'
        self.is_mac = self.os_type == 'darwin'
    
    async def execute_command(
        self,
        command: str,
        shell: bool = True,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """Execute a system command"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=shell
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "exit_code": process.returncode
            }
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_tool_installed(self, tool_name: str) -> Dict[str, Any]:
        """Check if a tool is installed"""
        if self.is_windows:
            command = f"where {tool_name}"
        else:
            command = f"which {tool_name}"
        
        result = await self.execute_command(command)
        
        return {
            "installed": result["success"],
            "path": result["stdout"].strip() if result["success"] else None,
            "tool": tool_name
        }
    
    async def install_chocolatey(self) -> Dict[str, Any]:
        """Install Chocolatey package manager on Windows"""
        if not self.is_windows:
            return {"success": False, "error": "Chocolatey is Windows-only"}
        
        # Check if already installed
        check = await self.check_tool_installed("choco")
        if check["installed"]:
            return {
                "success": True,
                "message": "Chocolatey already installed",
                "path": check["path"]
            }
        
        # Install Chocolatey
        command = """
        Set-ExecutionPolicy Bypass -Scope Process -Force;
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
        iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        """
        
        result = await self.execute_command(f"powershell -Command \"{command}\"", timeout=600)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Chocolatey installed successfully",
                "output": result["stdout"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error") or result["stderr"]
            }
    
    async def install_minikube(self) -> Dict[str, Any]:
        """Install Minikube for local Kubernetes"""
        # Check if already installed
        check = await self.check_tool_installed("minikube")
        if check["installed"]:
            return {
                "success": True,
                "message": "Minikube already installed",
                "path": check["path"]
            }
        
        if self.is_windows:
            # Ensure Chocolatey is installed
            choco_result = await self.install_chocolatey()
            if not choco_result["success"]:
                return choco_result
            
            # Install via Chocolatey
            result = await self.execute_command("choco install minikube -y", timeout=600)
            
        elif self.is_linux:
            commands = [
                "curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64",
                "sudo install minikube-linux-amd64 /usr/local/bin/minikube",
                "rm minikube-linux-amd64"
            ]
            result = await self.execute_command(" && ".join(commands), timeout=600)
            
        elif self.is_mac:
            result = await self.execute_command("brew install minikube", timeout=600)
        
        else:
            return {"success": False, "error": f"Unsupported OS: {self.os_type}"}
        
        if result["success"]:
            return {
                "success": True,
                "message": "Minikube installed successfully",
                "output": result["stdout"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error") or result["stderr"],
                "output": result["stdout"]
            }
    
    async def install_kubectl(self) -> Dict[str, Any]:
        """Install kubectl CLI"""
        check = await self.check_tool_installed("kubectl")
        if check["installed"]:
            return {
                "success": True,
                "message": "kubectl already installed",
                "path": check["path"]
            }
        
        if self.is_windows:
            choco_result = await self.install_chocolatey()
            if not choco_result["success"]:
                return choco_result
            
            result = await self.execute_command("choco install kubernetes-cli -y", timeout=600)
            
        elif self.is_linux:
            commands = [
                "curl -LO \"https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl\"",
                "sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl",
                "rm kubectl"
            ]
            result = await self.execute_command(" && ".join(commands), timeout=600)
            
        elif self.is_mac:
            result = await self.execute_command("brew install kubectl", timeout=600)
        
        else:
            return {"success": False, "error": f"Unsupported OS: {self.os_type}"}
        
        if result["success"]:
            return {
                "success": True,
                "message": "kubectl installed successfully",
                "output": result["stdout"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error") or result["stderr"]
            }
    
    async def start_minikube(self, driver: str = "docker") -> Dict[str, Any]:
        """Start Minikube cluster"""
        check = await self.check_tool_installed("minikube")
        if not check["installed"]:
            return {
                "success": False,
                "error": "Minikube not installed. Install it first."
            }
        
        # Check if already running
        status = await self.execute_command("minikube status", timeout=30)
        if "Running" in status["stdout"]:
            return {
                "success": True,
                "message": "Minikube is already running",
                "status": status["stdout"]
            }
        
        # Start Minikube
        command = f"minikube start --driver={driver}"
        result = await self.execute_command(command, timeout=600)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Minikube started successfully",
                "output": result["stdout"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error") or result["stderr"],
                "output": result["stdout"]
            }
    
    async def stop_minikube(self) -> Dict[str, Any]:
        """Stop Minikube cluster"""
        result = await self.execute_command("minikube stop", timeout=120)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Minikube stopped successfully",
                "output": result["stdout"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error") or result["stderr"]
            }
    
    async def get_cluster_status(self) -> Dict[str, Any]:
        """Get status of all Kubernetes clusters"""
        results = {}
        
        # Check Minikube
        minikube_check = await self.check_tool_installed("minikube")
        if minikube_check["installed"]:
            status = await self.execute_command("minikube status", timeout=30)
            results["minikube"] = {
                "installed": True,
                "running": "Running" in status["stdout"],
                "status": status["stdout"]
            }
        else:
            results["minikube"] = {"installed": False}
        
        # Check kubectl connection
        kubectl_check = await self.check_tool_installed("kubectl")
        if kubectl_check["installed"]:
            cluster_info = await self.execute_command("kubectl cluster-info", timeout=30)
            results["kubectl"] = {
                "installed": True,
                "connected": cluster_info["success"],
                "cluster_info": cluster_info["stdout"] if cluster_info["success"] else None
            }
        else:
            results["kubectl"] = {"installed": False}
        
        return {
            "success": True,
            "clusters": results,
            "summary": self._generate_status_summary(results)
        }
    
    def _generate_status_summary(self, results: Dict) -> str:
        """Generate human-readable status summary"""
        summary = []
        
        if results.get("minikube", {}).get("installed"):
            if results["minikube"].get("running"):
                summary.append("✅ Minikube is running")
            else:
                summary.append("⚠️ Minikube installed but not running")
        else:
            summary.append("❌ Minikube not installed")
        
        if results.get("kubectl", {}).get("installed"):
            if results["kubectl"].get("connected"):
                summary.append("✅ kubectl connected to cluster")
            else:
                summary.append("⚠️ kubectl installed but not connected")
        else:
            summary.append("❌ kubectl not installed")
        
        return "\n".join(summary)


# Global instance
system_executor = SystemExecutor()
