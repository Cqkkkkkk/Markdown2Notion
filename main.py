import dataclasses
import os
import pdb
import click
import mistune
import notion_client
from notionfier.converter import Converter

from notionfier.plugins.my_math import math
# from mistune.plugins.math import math, math_in_list, math_in_quote


@click.group()
def cli():
    pass


@cli.command
@click.option("--token", type=str, required=True, help="The Notion auth token.")
@click.option("--parent_page_id", type=str, required=True, help="The page id of the parent page.")
@click.option("--file_path", type=str, required=True, help="Path to your markdown file.")
def import_notion(token: str, parent_page_id: str, file_path: str):
    with open(file_path, "r", encoding="utf-8") as fi:
        content = fi.read()
    content = content.replace('$$', '\n')
    md = mistune.create_markdown(
        renderer=None,
        plugins=[math, 'table', 'task_lists'],
    )
    result = md(content)

    pdb.set_trace()
    converter = Converter()
    notion_result = converter.process(result)
    notion_result_without_linebreak = []

    for ele in notion_result:
        if str(ele) != r"Text(annotations=None, text=Text.Content(content='\n', link=None))":
            notion_result_without_linebreak.append(ele)

    params = {
        "parent": {"page_id": parent_page_id},
        "properties": {"title": {"title": [{"text": {"content": os.path.basename(file_path)}}]}},
        "children": [
            dataclasses.asdict(x, dict_factory=lambda x: {k: v for (k, v) in x if v is not None}) for x in notion_result_without_linebreak
        ],
    }

    client = notion_client.Client(auth=token)
    client.pages.create(**params)


if __name__ == "__main__":
    cli()
