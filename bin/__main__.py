import argparse
import shlex
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent.parent


def parse_command_line_args() -> argparse.Namespace:
    """Parse command line arguments for the OneRoof pipeline.

    This function sets up an argument parser with various subcommands and their
    respective arguments. The subcommands include 'env', 'validate', 'resume',
    and 'run', each with its own set of options.

    Returns:
        argparse.Namespace: An object containing all the parsed arguments.

    Subcommands:
        env: Check that all dependencies are available in the environment.
        validate: Validate provided inputs.
        resume: Resume the previous run.
        run: Run the full pipeline.

    The 'run' subcommand has numerous options for configuring the pipeline,
    including input files, reference sequences, basecalling parameters,
    and various thresholds for filtering and analysis.
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="Subcommands", dest="subcommands")

    # create the env subcommand
    _env = subparsers.add_parser(
        "env",
        help="Check that all dependencies are available in the environment",
    )

    # create the validate subcommand
    _validate = subparsers.add_parser("validate", help="Validate provided inputs.")

    # create the resume subcommand
    resume = subparsers.add_parser("resume", help="Resume the previous run.")
    resume.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (-v for WARNING, -vv for INFO, -vvv for DEBUG)",
        required=False,
    )

    # create the run subcommand
    run = subparsers.add_parser("run", help="Run the full pipeline.")
    run.add_argument(
        "--primer_bed",
        type=str,
        default=None,
        help="A bed file of primer coordinates relative to the reference provided with"
        "the parameters `refseq` and `ref_gbk`.",
    )
    run.add_argument(
        "--fwd_suffix",
        type=str,
        default=None,
        help="Suffix in the primer bed file denoting forward primer",
    )
    run.add_argument(
        "--rev_suffix",
        type=str,
        default=None,
        help="Suffix in the primer bed file denoting reverse primer",
    )
    run.add_argument(
        "--refseq",
        type=str,
        required=True,
        help="The reference sequence to be used for mapping in FASTA format.",
    )
    run.add_argument(
        "--ref_gbk",
        type=str,
        default=None,
        help="The reference sequence to be used for variant annotation in Genbank"
        "format.",
    )
    run.add_argument(
        "--remote_pod5_location",
        type=str,
        default=None,
        help="A remote location to use with a ssh client to watch for pod5 files in"
        "realtime as they are generated by the sequencing instrument.",
    )
    run.add_argument(
        "--file_watcher_config",
        type=str,
        default=None,
        help="Configuration file for remote file monitoring.",
    )
    run.add_argument(
        "--pod5_staging",
        type=str,
        default=None,
        help="Where to cache pod5s as they arrive from the remote location",
    )
    run.add_argument(
        "--pod5_dir",
        type=str,
        default=None,
        help="A local, on-device directory where pod5 files have been manually"
        "transferred.",
    )
    run.add_argument(
        "--precalled_staging",
        type=str,
        default=None,
        help="A local directory to watch for Nanopore FASTQs or BAMs as they become"
        "available.",
    )
    run.add_argument(
        "--prepped_data",
        type=str,
        default=None,
        help="Location of already basecalled and demultiplexed pod5 files.",
    )
    run.add_argument(
        "--illumina_fastq_dir",
        type=str,
        default=None,
        help="Location of Illumina paired-end FASTQ files.",
    )
    run.add_argument(
        "--model",
        type=str,
        default=None,
        help="The Nanopore basecalling model to apply to the provided pod5 data.",
    )
    run.add_argument(
        "--model_cache",
        type=str,
        default=None,
        help="Where to cache the models locally.",
    )
    run.add_argument(
        "--kit",
        type=str,
        default=None,
        help="The Nanopore barcoding kit used to prepare sequencing libraries.",
    )
    run.add_argument(
        "--pod5_batch_size",
        type=int,
        default=None,
        help="How many pod5 files to basecall at once.",
    )
    run.add_argument(
        "--basecall_max",
        type=int,
        default=None,
        help="How many parallel instances of the basecaller to run at once.",
    )
    run.add_argument(
        "--max_len",
        type=int,
        default=None,
        help="The maximum acceptable length for a given read.",
    )
    run.add_argument(
        "--min_len",
        type=int,
        default=None,
        help="The minimum acceptable length for a given read.",
    )
    run.add_argument(
        "--min_qual",
        type=int,
        default=None,
        help="The minimum acceptable average quality for a given read.",
    )
    run.add_argument(
        "--secondary",
        action="store_true",
        help="Whether to turn on secondary alignments for each amplicon.",
    )
    run.add_argument(
        "--max_mismatch",
        type=int,
        default=None,
        help="The maximum number of mismatches to allow when finding primers.",
    )
    run.add_argument(
        "--downsample_to",
        type=int,
        default=None,
        help="Desired coverage to downsample to, with 0 indicating no downsampling.",
    )
    run.add_argument(
        "--min_consensus_freq",
        type=float,
        default=None,
        help="The minimum required frequency of a variant base to be included in a"
        "consensus sequence.",
    )
    run.add_argument(
        "--min_haplo_reads",
        type=int,
        default=None,
        help="The minimum required read support to report an amplicon-haplotype.",
    )
    run.add_argument(
        "--snpeff_cache",
        type=str,
        default=None,
        help="Where to cache a custom snpEff database.",
    )
    run.add_argument(
        "--min_depth_coverage",
        type=int,
        default=None,
        help="Minimum depth of coverage [default: 20].",
    )
    run.add_argument("--nextclade_dataset", type=str, help="Nextclade dataset.")
    run.add_argument(
        "--nextclade_cache",
        type=str,
        default=None,
        help="Nextclade dataset cache.",
    )
    run.add_argument(
        "--results",
        type=str,
        default=None,
        help="Where to place results.",
    )
    run.add_argument(
        "--cleanup",
        action="store_true",
        help="Whether to cleanup work directory after a successful run.",
    )
    run.add_argument(
        "--resume",
        action="store_true",
        help="Whether to resume from a previous run.",
    )
    run.add_argument(
        "--snpEff_config",
        type=str,
        default=None,
        help="snpEff config file.",
    )
    run.add_argument(
        "-profile",
        type=str,
        nargs="+",
        choices=["standard", "docker", "singularity", "apptainer", "containerless"],
        default=None,
        help="The run configuration profile to use.",
    )

    return parser.parse_args()


def generate_nextflow_command(args: argparse.Namespace) -> str:
    """Generate a Nextflow command based on the provided arguments.

    This function takes the parsed command-line arguments and converts them into
    a Nextflow command string. It filters out None values and handles boolean flags
    appropriately.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.

    Returns:
        str: A string representing the complete Nextflow command to be executed.

    The function performs the following steps:
    1. Converts the argparse.Namespace to a dictionary.
    2. Filters out None values and creates Nextflow parameter strings.
    3. Handles boolean flags by including only the parameter name if True.
    4. Joins all parameters into a single string.
    5. Constructs and returns the full Nextflow command.
    """
    # Convert the namespace to a dictionary
    args_dict = {k: v for k, v in vars(args).items() if k != "subcommands"}

    # Filter out None values and create Nextflow parameter strings
    nextflow_params = []
    for arg, value in args_dict.items():
        if value is not None:
            if isinstance(value, bool):
                # For boolean flags, just include the parameter name if True
                if value:
                    nextflow_params.append(f"--{arg}")
            else:
                # For other types, include the value
                nextflow_params.append(f"--{arg} {shlex.quote(str(value))}")

    # Join all parameters into a single string
    params_str = " ".join(nextflow_params)

    # Construct and return the full Nextflow command
    return f"nextflow run . {params_str}"


def run_nextflow(run_command: str) -> None:
    """Run the Nextflow command.

    This function executes the provided Nextflow command, handles resuming a previous run,
    and writes the command to a file for future resumption.

    Args:
        run_command (str): The Nextflow command to be executed.

    Returns:
        None

    The function performs the following steps:
    1. Writes the run command to a '.nfresume' file, appending '-resume' if not already present.
    2. If the command ends with '-resume', it only writes to the file and returns.
    3. Splits the command into a list and executes it using subprocess.run().
    """

    with Path(".nfresume").open("w", encoding="utf8") as resume_handle:
        if run_command.endswith("-resume"):
            resume_handle.write(run_command)
            return
        resume_handle.write(f"{run_command} -resume")

    split_command = run_command.split("")
    subprocess.run(split_command, check=True)
    return


def resume_nextflow() -> None:
    """Resume a previous Nextflow run.

    This function resumes a previously executed Nextflow run by reading the command
    from a '.nfresume' file and executing it. It checks for the existence of the
    '.nfresume' file before proceeding.

    Raises:
        AssertionError: If the '.nfresume' file does not exist, indicating that no
        previous run was detected.

    Returns:
        None

    The function performs the following steps:
    1. Checks for the existence of the '.nfresume' file.
    2. Reads the Nextflow command from the '.nfresume' file.
    3. Calls the run_nextflow() function with the read command to resume the run.
    """

    assert Path(
        ".nfresume",
    ).exists(), "Previous run not detected. Make sure you start with `oneroof run`"
    "before switching to `oneroof resume`."

    with Path(".nfresume").open("r", encoding="utf8") as resume_handle:
        run_command = resume_handle.readline().strip()
    run_nextflow(run_command)


def main() -> None:
    """Main function serving as the entry point for the OneRoof pipeline.

    This function orchestrates the execution of the pipeline based on the chosen subcommand.
    It parses command-line arguments, validates the subcommand, and invokes the appropriate
    function for running or resuming the Nextflow pipeline.

    The function supports the following subcommands:
    - 'run': Executes a new pipeline run with the provided arguments.
    - 'resume': Resumes a previously executed pipeline run.
    - Other subcommands (e.g., 'env', 'validate') are recognized but not yet implemented.

    Raises:
        AssertionError: If an invalid number of subcommands is detected.
        SystemExit: If an unsupported subcommand is provided.

    Returns:
        None

    The function performs the following steps:
    1. Parses command-line arguments.
    2. Validates that exactly one subcommand is chosen.
    3. Executes the appropriate action based on the chosen subcommand:
       - For 'run', generates and executes a Nextflow command.
       - For 'resume', resumes a previous Nextflow run.
       - For other subcommands, exits with an informative message.
    """

    args = parse_command_line_args()
    chosen_subcommand = [v for k, v in vars(args).items() if k == "subcommands"]
    assert (
        len(chosen_subcommand) == 1
    ), "Invalid state registered in the form of requesting more than one or zero sub"
    f"commands: {chosen_subcommand}"

    subcommand = chosen_subcommand[0]
    match subcommand:
        case "run":
            run_command = generate_nextflow_command(args)
            run_nextflow(run_command)
        case "resume":
            resume_nextflow()
        case _:
            sys.exit(
                f"The subcommand {subcommand} is not yet supported but will be soon!",
            )


if __name__ == "__main__":
    main()