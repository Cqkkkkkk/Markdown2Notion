# MyNotionfier [Forked]: Import Markdown Pages to Notion.so

Import markdown files to Notion.so using its [official API](https://developers.notion.com/).

This project is forked from [Notionfier](https://github.com/Arsenal591/notionfier.git). I updated the core dependency package [Mistune](https://mistune.lepture.com) from version 2.0 to version 3.0, to support inline math phrase. With such a update, fundamental changes occurs to the original code.

- The behaviour of this project is non-stable. Use it cautiously.
- If required by the [original onwer](https://github.com/Arsenal591/notionfier.git), I would delete the repo.



**Requirments**: Python >= 3.7.

## Features
- All markdown basic syntax.
- Some markdown extended syntax:
  - Tables.
  - Code blocks.
  - Inline math.
  - Task lists.
  - Automatic URL Linking.

Note: Block math is currently not supported, as the math pharse provided by Mistune is still buggy. 
- For example, multi-line math block pharsing is currently not supported by the package.
- If you want to enable it (which will probably bring bugs and errors), go `notionfier/plugins/my_math.py` and uncomment all the commented codes.


## Usage

- Firstly, follow the [instruction](https://developers.notion.com/docs/getting-started) to create an notion integration and share a page with the integration.
- Run the Python script:

```
python main.py import-notion --token={{YOUR NOTION TOKEN}} --parent_page_id={{PAGE ID}} --file_path={{FILE PATH}}
```
- The script will import the markdown file to Notion. A new page under `parent_page_id` will be created with the content.


## TODOs
- [ ] MathJax for block math

## LICENSE
[MIT License](https://opensource.org/licenses/MIT)