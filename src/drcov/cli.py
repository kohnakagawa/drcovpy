import io
import os

import typer

from .core import DrCov

app = typer.Typer()


@app.command()
def extract_specific_cov_info(
    in_file_path: str, out_file_path: str, module_name: str
) -> None:
    dr_cov = DrCov()
    dr_cov.import_from_file(in_file_path)
    dr_cov.export_specific_module_to_file(module_name, out_file_path)


@app.command()
def show_specific_cov_info(in_file_path: str, module_name: str) -> None:
    dr_cov_in = DrCov()
    dr_cov_in.import_from_file(in_file_path)
    bio = io.BytesIO()
    dr_cov_in.export_specific_module_to_binaryio(bio, module_name)
    bio.seek(0)

    dr_cov_out = DrCov()
    dr_cov_out.import_from_binaryio(bio)
    typer.echo(str(dr_cov_out))


@app.command()
def show_all_cov_info(in_file_path: str) -> None:
    dr_cov = DrCov()
    dr_cov.import_from_file(in_file_path)
    typer.echo(str(dr_cov))
