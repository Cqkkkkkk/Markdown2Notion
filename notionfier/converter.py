import dataclasses
from typing import Any, List, Optional, Tuple

import mistune.renderers
import pdb
from notionfier.api.block_objects import (
    BlockObject,
    BulletedListItem,
    Code,
    Divider,
    Heading1,
    Heading2,
    Heading3,
    Image,
    NumberedListItem,
    Paragraph,
    Quote,
    Table,
    TableRow,
    Todo,
    Equation,
)
from notionfier.api.common_objects import Annotation, ExternalFile, LinkObject, RichText, Text
from notionfier.api.consts import CodeLanguage
from notionfier.api.utils import NotionObject


def _split_list_of_notion_objects(notion_objects: List[NotionObject],) -> Tuple[List[RichText], List[BlockObject]]:
    rich_texts: List[RichText] = []
    block_objects: List[BlockObject] = []
    for obj in notion_objects:
        if isinstance(obj, RichText):
            rich_texts.append(obj)
        elif isinstance(obj, BlockObject):
            block_objects.append(obj)
    return rich_texts, block_objects


def _process_annotation(text: RichText, key: str, value: Any) -> RichText:
    if text.annotations is None:
        text.annotations = Annotation()
    setattr(text.annotations, key, value)
    return text



@dataclasses.dataclass
class MyText(RichText):
    @dataclasses.dataclass
    class Equation:
        class Expression:
            content: str
        expression: Expression
        
    equation: Equation = Equation(expression="")
    


class Converter():
    def __init__(self):
        pass

    def process(self, md):
        return self.render_tokens(md)
        

    def render_token(self, token):
       
        func = self._get_method(token['type'])
        
        attrs = token.get('attrs')
            
        if 'raw' in token:
            text = token['raw']
        elif 'children' in token:
            text = self.render_tokens(token['children'])
        else:
            if attrs: 
                return func(**attrs)
            else:
                return func()
        if attrs:
            if token['type'] == 'link':
                pdb.set_trace()
            return func(text, **attrs)
        else:
            try: 
                return func(text)
            except TypeError:
                pdb.set_trace()


    def render_tokens(self, tokens):
        tmp = self.iter_tokens(tokens)
        # pdb.set_trace()
        flt_tmp = []
        for tok in tmp:
            flt_tmp = flt_tmp + tok
        return flt_tmp


    def _get_method(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pdb.set_trace()
            method = self.__methods.get(name)
            if not method:
                raise AttributeError('No renderer "{!r}"'.format(name))
            return method


    def iter_tokens(self, tokens):
        result = []
        for tok in tokens:
            result.append(self.render_token(tok))
        return result
    


    def text(self, text: str):
        assert isinstance(text, str)
        return [Text(text=Text.Content(content=text))]

    def link(
        self,
        text: str,
        url: str,
        children_objects: Optional[List[NotionObject]] = None,
    ):
        children_objects = children_objects or []
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        assert len(block_objects) == 0
        result = []
        if len(text_objects) > 0:
            for obj in text_objects:
                assert isinstance(obj, Text)  # todo: check this
                result.append(
                    Text(
                        text=Text.Content(content=obj.text.content, link=LinkObject(url=url)),
                        annotations=obj.annotations,
                    )
                )
        else:
            result.append(Text(text=Text.Content(content=text[0].text.content, link=LinkObject(url=url))))
        return result

    def image(self, text, url, alt=None, title: Optional[List[NotionObject]] = None):
        # todo: image caption
        block = Image(
            image=Image.Content(
                external=ExternalFile(url=url), caption=[Text(text=Text.Content(content=''))]
            )
        )
        return [block]

    def emphasis(self, children_objects: List[NotionObject]):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        assert len(block_objects) == 0
        return [_process_annotation(x, "italic", True) for x in text_objects]

    def strong(self, children_objects: List[NotionObject]):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        assert len(block_objects) == 0
        return [_process_annotation(x, "bold", True) for x in text_objects]

    def codespan(self, code: str):
        return [Text(text=Text.Content(content=code), annotations=Annotation(code=True))]

    def linebreak(self):
        return [Text(text=Text.Content(content="\n"))]

    def softbreak(self):
        return [Text(text=Text.Content(content="\n"))]

    def blank_line(self):
        return [Text(text=Text.Content(content="\n"))]

    def inline_html(self, html):
        return [Text(text=Text.Content(content=html))]

    def inline_math(self, math):
        return [MyText(equation=MyText.Equation(expression=math))]
        # return 

    def paragraph(self, children_objects: List[NotionObject]):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        return [
            Paragraph(
                paragraph=Paragraph.Content(rich_text=text_objects, children=block_objects or None)
            )
        ]

    def heading(self, children_objects: List[NotionObject], level: int):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        assert len(block_objects) == 0
        max_level = 2
        if level > max_level:
            level = max_level

        if level == 1:
            return [Heading1(heading_1=Heading1.Content(rich_text=text_objects))]
        else:
            return [Heading2(heading_2=Heading2.Content(rich_text=text_objects))]

    def newline(self):
        return []

    def thematic_break(self):
        return [Divider()]

    def block_text(self, children_objects: List[NotionObject]):
        return children_objects

    def block_code(self, code: str, info: Optional[str] = None):
        block = Code(code=Code.Content(rich_text=[Text(text=Text.Content(content=code))]))
        if info is not None:
            language = info.strip().lower()

            # todo: consider aliases, like js-javascript
            if language in CodeLanguage.__members__:
                block.code.language = CodeLanguage(language)

        return [block]

    def block_quote(self, children_objects: List[NotionObject]):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        assert len(text_objects) == 0

        rich_text = []
        children = []
        if len(block_objects) > 0:
            first_obj = block_objects[0]
            if isinstance(first_obj, Paragraph):
                rich_text = first_obj.paragraph.rich_text
                children = block_objects[1:]
            elif isinstance(first_obj, Heading1):
                rich_text = first_obj.heading_1.rich_text
                children = block_objects[1:]
            elif isinstance(first_obj, Heading2):
                rich_text = first_obj.heading_2.rich_text
                children = block_objects[1:]
            elif isinstance(first_obj, Heading3):
                rich_text = first_obj.heading_3.rich_text
                children = block_objects[1:]
            else:
                children = block_objects
        return [Quote(quote=Quote.Content(rich_text=rich_text, children=children or None))]

    def block_html(self, html: str):
        return [
            Paragraph(
                paragraph=Paragraph.Content(rich_text=[Text(text=Text.Content(content=html))])
            )
        ]

    def block_error(self, html):
        return [
            Paragraph(
                paragraph=Paragraph.Content(rich_text=[Text(text=Text.Content(content=html))])
            )
        ]

    def block_math(self, math):
        return [
            Equation(Equation.Content(expression=math))
        ]

    def list(self, children_objects: List[NotionObject], ordered, level=None, start=None):
        # pdb.set_trace()
        if not ordered:
            return children_objects

        result = []

        for child in children_objects:
            assert isinstance(child, BulletedListItem)
            result.append(
                NumberedListItem(
                    numbered_list_item=NumberedListItem.Content(
                        rich_text=child.bulleted_list_item.rich_text,
                        children=child.bulleted_list_item.children,
                        color=child.bulleted_list_item.color,
                    )
                )
            )
        return result

    def list_item(self, children_objects: List[NotionObject], level=None):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        if len(text_objects) == 0 and len(block_objects) > 0:
            first_block = block_objects[0]
            if isinstance(first_block, Paragraph):
                text_objects = first_block.paragraph.rich_text
                block_objects = block_objects[1:]
        return [
            BulletedListItem(
                bulleted_list_item=BulletedListItem.Content(
                    rich_text=text_objects, children=block_objects or None
                )
            )
        ]

    def footnote_ref(self, key, index, dup):
        return [Text(text=Text.Content(content=f"[{index}]"))]

    def footnotes(self, children_objects: List[NotionObject]):
        result: List[NotionObject] = [Divider()]
        return result + children_objects

    def footnote_item(self, children_objects: List[NotionObject], key, index, is_inline_text):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        if len(text_objects) == 0 and len(block_objects) > 0:
            first_block = block_objects[0]
            if isinstance(first_block, Paragraph):
                text_objects = first_block.paragraph.rich_text
                block_objects = block_objects[1:]
        return [
            NumberedListItem(
                numbered_list_item=NumberedListItem.Content(
                    rich_text=text_objects, children=block_objects
                )
            )
        ]

    def strikethrough(self, children_objects: List[NotionObject]):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        assert len(block_objects) == 0
        return [_process_annotation(x, "strikethrough", True) for x in text_objects]

    def def_list(self, children_objects: List[NotionObject]):
        return children_objects

    def def_list_header(self, children_objects: List[NotionObject]):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        assert len(block_objects) == 0
        for obj in text_objects:
            if obj.annotations is None:
                obj.annotations = Annotation()
            obj.annotations.bold = True
            obj.annotations.italic = True
        return [Paragraph(paragraph=Paragraph.Content(rich_text=text_objects))]

    def def_list_item(self, children_objects: List[NotionObject]):
        # todo: support multi-paragraph def list items
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        if len(text_objects) == 0 and len(block_objects) > 0:
            first_block = block_objects[0]
            if isinstance(first_block, Paragraph):
                text_objects = first_block.paragraph.rich_text
                block_objects = block_objects[1:]
        result: List[BlockObject] = [Paragraph(paragraph=Paragraph.Content(rich_text=text_objects))]
        return result + block_objects

    def table(self, children_objects: List[NotionObject]):
        assert len(children_objects) > 0
        width = 0
        for obj in children_objects:
            assert isinstance(obj, TableRow)
            width = len(obj.table_row.cells)
        return [
            Table(
                table=Table.Content(
                    table_width=width,
                    has_row_header=False,
                    has_column_header=True,
                    children=children_objects,  # type: ignore
                )
            )
        ]

    def table_head(self, children_objects: List[NotionObject]):
        all_cells: List[List[RichText]] = []
        for obj in children_objects:
            assert isinstance(obj, TableRow)
            all_cells.append(obj.table_row.cells[0])
        return [TableRow(table_row=TableRow.Content(cells=all_cells))]

    def table_body(self, children_objects: List[NotionObject]):
        for obj in children_objects:
            assert isinstance(obj, TableRow)
        return children_objects

    def table_row(self, children_objects: List[NotionObject]):
        all_cells: List[List[RichText]] = []
        for obj in children_objects:
            assert isinstance(obj, TableRow)
            all_cells.append(obj.table_row.cells[0])
        return [TableRow(table_row=TableRow.Content(cells=all_cells))]

    def table_cell(self, children_objects: List[NotionObject], align=None, head=False):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        assert len(block_objects) == 0

        # A little hack here: we use `TableRow` as a temporary container for a table cell.
        return [TableRow(table_row=TableRow.Content(cells=[text_objects]))]

    def task_list_item(self, children_objects: List[NotionObject], checked: bool):
        text_objects, block_objects = _split_list_of_notion_objects(children_objects)
        if len(text_objects) == 0 and len(block_objects) > 0:
            first_block = block_objects[0]
            if isinstance(first_block, Paragraph):
                text_objects = first_block.paragraph.rich_text
                block_objects = block_objects[1:]
        return [
            Todo(
                to_do=Todo.Content(
                    rich_text=text_objects, children=block_objects or None, checked=checked
                )
            )
        ]

    def finalize(self, data):
        return [item for sublist in data for item in sublist]
