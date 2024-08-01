import json
from pathlib import Path
import re


def main() -> None:
    question_files = Path('questions').glob('*.txt')
    questions = {}
    for file in question_files:
        print(file)
        with open(file, 'r', encoding='KOI8-R') as stream:
            content = stream.read().split('\n\n')

        i = 0
        while i < len(content):
            question = re.match(r'Вопрос \d+:\n', content[i])
            if question:
                questions[question.string] = content[i+1]
                i += 2
            else:
                i += 1
    with open('questions.json', 'w', encoding='utf-8') as stream:
        stream.write(json.dumps(questions, ensure_ascii=False, indent=2))
    return questions


if __name__ == '__main__':
    main()
