# Vuulgaris V1 - Daisy Patch SM firmware
#
# BOOT_SRAM is deliberate, not a default. See docs/decisions/0008-boot-sram-not-qspi.md:
# BOOT_QSPI runs from QSPI and can grow to ~7.75MB, which eats the sample space.

TARGET = vuulgaris

APP_TYPE = BOOT_SRAM

# Sources
CPP_SOURCES = src/main.cpp

# Library locations
LIBDAISY_DIR = ./libDaisy
DAISYSP_DIR  = ./DaisySP

# Core location, and generic Makefile
SYSTEM_FILES_DIR = $(LIBDAISY_DIR)/core
include $(SYSTEM_FILES_DIR)/Makefile

# ---- convenience targets -------------------------------------------------
.PHONY: libs clean-libs program-dfu-boot

## Build both submodules. Run once after cloning.
libs:
	$(MAKE) -C $(LIBDAISY_DIR)
	$(MAKE) -C $(DAISYSP_DIR)

clean-libs:
	$(MAKE) -C $(LIBDAISY_DIR) clean
	$(MAKE) -C $(DAISYSP_DIR) clean
