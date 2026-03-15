package com.sysagent.sysagent_backend.model.enums;

/**
 * Enumeration representing the different operating systems supported by SysAgent.
 * Used to classify devices and determine which scripts are compatible.
 */
public enum DeviceType {
    /**
     * Microsoft Windows Operating System.
     */
    WINDOWS,

    /**
     * Linux-based Operating Systems (Ubuntu, Debian, CentOS, etc.).
     */
    LINUX,

    /**
     * Apple macOS.
     */
    MACOS,

    /**
     * Unknown or unidentified operating system.
     */
    UNKNOWN
}
