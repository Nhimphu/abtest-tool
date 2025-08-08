import xml.etree.ElementTree as ET
from pathlib import Path

def fill(path: Path) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    changed = False
    for message in root.findall('.//message'):
        source = message.find('source')
        translation = message.find('translation')
        if source is None:
            continue
        if translation is None:
            translation = ET.SubElement(message, 'translation')
        if translation.text != source.text:
            translation.text = source.text
            changed = True
        if 'type' in translation.attrib:
            del translation.attrib['type']
            changed = True
    if changed:
        tree.write(path, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    fill(Path('translations/app_ru.ts'))
    fill(Path('translations/app_en.ts'))
