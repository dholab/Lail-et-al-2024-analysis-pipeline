#!/usr/bin/env nextflow

include { GENERATE_MPILEUP } from "../modules/samtools"
include { CALL_VARIANTS; CONVERT_TO_VCF } from "../modules/ivar"
include { BUILD_DB; ANNOTATE_VCF } from "../modules/snpeff"

workflow VARIANTS {

    /* */

    take:
        ch_amplicons
        ch_refseq
        ch_genbank
        ch_snpeff_config

    main:
        GENERATE_MPILEUP (
            ch_amplicons
        )

        CALL_VARIANTS (
            GENERATE_MPILEUP.out,
            ch_refseq
        )

        CONVERT_TO_VCF (
            CALL_VARIANTS
        )

        BUILD_DB (
            ch_refseq,
            ch_genbank,
            ch_snpeff_config
        )

        ANNOTATE_VCF (
            BUILD_DB.out,
            ch_snpeff_config,
            ANNOTATE_VCF.out
        )

    // emit:
    //     ANNOTATE_VCF.out

}