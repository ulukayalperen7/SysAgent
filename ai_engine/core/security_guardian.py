import re

class SecurityGuardian:
    """
    Cross-platform protection layer.
    Ensures that even if AI generates a destructive script to a system directory, 
    it gets blocked before it ever reaches the user UI.
    """
    
    WINDOWS_RED_ZONES = [
        r"c:\\windows", r"c:\\program files", r"c:\\programdata", 
        r"c:\\users\\all users"
    ]
    
    LINUX_MAC_RED_ZONES = [
        r"/etc", r"/bin", r"/sbin", r"/usr/bin", r"/usr/sbin", 
        r"/root", r"/var/lib", r"/boot", r"/sys", r"/dev"
    ]
    
    BLACKLISTED_COMMANDS = ["rm -rf /", "mkfs", "dd if=", "shutdown", "reboot", "del /s /q c:\\"]

    @classmethod
    def validate_command(cls, command: str, os_name: str) -> tuple[bool, str]:
        """
        Validates if a script is safe to be prompted to the user.
        If it returns (False, reason), the script MUST NOT be shown as an executable UI task.
        """
        if not command or command.strip().upper() == "NONE":
            return True, "Boş veya NONE komut."

        cmd_lower = command.lower()
        
        # 1. Check Hard Blacklist
        for bad_cmd in cls.BLACKLISTED_COMMANDS:
            if bad_cmd in cmd_lower:
                return False, f"Güvenlik İhlali: Kurumsal politikalar gereği '{bad_cmd}' içeren kritik sistem komutları kesinlikle engellenmiştir."
                
        # 2. Check Red Zones based on OS Context (Provided by Java Backend)
        is_windows = "windows" in os_name.lower()
        
        if is_windows:
            for zone in cls.WINDOWS_RED_ZONES:
                if zone in cmd_lower:
                    return False, f"Güvenlik İhlali: 'C:\\Windows' veya benzeri kritik sistem dizinlerine (Red Zone) dışarıdan müdahale edilemez."
        else:
            for zone in cls.LINUX_MAC_RED_ZONES:
                # Prevent matching "echo /etc" if we are just searching, but for now we strictly block ANY mention 
                # of red zones in commands to be safe. E.g "rm -rf /etc/..."
                # More robust: check if path is used as argument
                if f" {zone}" in cmd_lower or cmd_lower.startswith(f"{zone}"):
                    return False, f"Güvenlik İhlali: '{zone}' gibi kök/sistem dizinlerine (Red Zone) yazma veya silme işlemi engellenmiştir."

        return True, "Güvenli"
        
    @classmethod
    def requires_approval(cls, intent: str) -> bool:
        """
        Determines if the intent requires explicit user approval via UI.
        READ operations run autonomously inside Python without bothering the user.
        """
        SAFE_INTENTS = [
            "FILE_SYSTEM_READ", 
            "DEVOPS_READ", 
            "NETWORK_READ",     # Ping, nslookup 
            "CHAT"
        ]
        # Any WRITE, DELETE, or APP execution requires User UI Approval.
        return intent not in SAFE_INTENTS
