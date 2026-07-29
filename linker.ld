OUTPUT_ARCH(arm)
MEMORY {

		rom     : ORIGIN = (0x08000000 + 0x184d310), LENGTH = (0x0A000000 - (0x08000000 + 0x184d310))
        rom2    : ORIGIN = 0x09000000, LENGTH = 0x200000
        ewram   : ORIGIN = 0x02000000, LENGTH = 4M - 4k
}

SECTIONS {
        /* rom2 is file offset 0x1000000-0x1200000: the gap between the end of
           the 16MB source rom and the B2W2 music patch (which patches.py writes
           at 0x1200000 and which ends at 0x184D2FE, just below OFFSET_TO_PUT).
           Nothing else in the build chain reaches it -- CFRU inserts at
           0x830000 and every .ips record ends by 0xF100DC -- and HexManiac
           cannot allocate there because the rom it edits is only 16MB.
           Read-only data only: no code, and nothing a hook branches to. */
        .rom2 : {
                __rom2_start = . ;
                *(.rodata.rom2)
                . = ALIGN(4);
                __rom2_end = . ;
        } >rom2 = 0xff

        .text : {

                FILL (0xABCD)

                __text_start = . ;
                *(.init)
                *(.text)
                *(.ctors)
                *(.dtors)
                *(.rodata)
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