OUTPUT_ARCH(arm)
MEMORY {

		rom     : ORIGIN = (0x08000000 + 0x184d310), LENGTH = 0x7b2cf0
		rom2    : ORIGIN = (0x08000000 + 0x1000000), LENGTH = 2M
        ewram   : ORIGIN = 0x02000000, LENGTH = 4M - 4k
}

SECTIONS {
        .rom2 : {
                FILL (0xABCD)
                __rom2_start = . ;
                *IMG_iconsprites.o(.rodata .rodata.*)
                __rom2_end = . ;
        } >rom2 = 0xff

        .text : {

                FILL (0xABCD)

                __text_start = . ;
                *(.init)
                *(.text)
                *(.ctors)
                *(.dtors)
                EXCLUDE_FILE(*IMG_iconsprites.o) *(.rodata)
                *(.fini)
                *(COMMON)
                __text_end  = . ;

                __bss_start__ = . ;
                *(.bss)
                __bss_end__ = . ;
        _end = __bss_end__ ;
        __end__ = __bss_end__ ;
        } >rom = 0xff
}