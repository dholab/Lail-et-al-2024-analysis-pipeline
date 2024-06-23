#!/usr/bin/env nextflow

// include { RESPLICE_PRIMERS } from "../modules/resplice_primers"
include { SPLIT_PRIMER_COMBOS } from "../modules/split_primer_combos"
include { GET_PRIMER_PATTERNS } from "../modules/primer_patterns"
include { GET_PRIMER_SEQS } from "../modules/bedtools"
include { TRIM_ENDS_TO_PRIMERS } from "../modules/cutadapt"
include { FASTQ_CONVERSION; FAIDX } from "../modules/samtools"
include { ORIENT_READS } from "../modules/vsearch"
include {
    FIND_COMPLETE_AMPLICONS;
    MERGE_BY_SAMPLE;
    AMPLICON_STATS
} from "../modules/seqkit"
include { RASUSA_READS } from "../modules/rasusa"

// use some Groovy to count the number of amplicons
import java.nio.file.Files
import java.nio.file.Paths
import java.util.stream.Collectors

def countAmplicons(String filePath) {
    // Read all lines from the file
    def lines = Files.readAllLines(Paths.get(filePath))

    // Extract the fourth column, replace hyphens, and remove _LEFT and _RIGHT
    def processedItems = lines.collect { line ->
        def columns = line.split('\t')
        if (columns.size() >= 4) {
            def item = columns[3]
            item = item.replace('-', '_')
            item = item.replace('_LEFT', '').replace('_RIGHT', '')
            return item
        }
        return null
    }.findAll { it != null }

    // Convert to a set to find unique items
    def uniqueItems = processedItems.toSet()

    // Return the number of unique items
    return uniqueItems.size()
}
int ampliconCount = countAmplicons(params.primer_bed)


workflow PRIMER_HANDLING {

    /* */

    take:
        ch_basecalls
        ch_primer_bed
        ch_refseq

    main:
        // RESPLICE_PRIMERS (
        //     ch_primer_bed
        // )

        SPLIT_PRIMER_COMBOS (
            ch_primer_bed
        )

        GET_PRIMER_SEQS (
            SPLIT_PRIMER_COMBOS.out.flatten(),
            ch_refseq
        )

        GET_PRIMER_PATTERNS (
            GET_PRIMER_SEQS.out
        )

        FASTQ_CONVERSION (
            ch_basecalls
        )

        ORIENT_READS (
            FASTQ_CONVERSION.out
                .map { barcode, fastq -> tuple( barcode, file(fastq), file(fastq).countFastq() ) }
                .filter { it[2] > 100 }
                .map { barcode, fastq, read_count -> tuple( barcode, file(fastq) ) },
            ch_refseq
        )

        FIND_COMPLETE_AMPLICONS (
            ORIENT_READS.out
                .map { barcode, fastq -> fastq }
                .combine ( GET_PRIMER_PATTERNS.out )
        )

        TRIM_ENDS_TO_PRIMERS (
            FIND_COMPLETE_AMPLICONS.out
        )

        AMPLICON_STATS (
            TRIM_ENDS_TO_PRIMERS.out.groupTuple( by: 0, size: ampliconCount )
        )

        MERGE_BY_SAMPLE (
            TRIM_ENDS_TO_PRIMERS.out.groupTuple( by: 0, size: ampliconCount )
        )

        FAIDX (
            MERGE_BY_SAMPLE.out
        )

        RASUSA_READS (
            FAIDX.out
        )

    emit:
        RASUSA_READS.out
}
