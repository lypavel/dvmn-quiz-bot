import json
from pathlib import Path
import re

from environs import Env


def check_answer(user_answer: str, correct_answer: str) -> bool:
    correct_answer = remove_clarifications(correct_answer)
    if user_answer.lower() == correct_answer.split('.', 1)[0].lower():
        return True
    return False


def remove_clarifications(text: str) -> str:
    for left_bracket, right_bracket in (('[', ']'), ('(', ')'), ('{', '}')):
        if text.startswith(left_bracket) and right_bracket in text:
            splitted_text = text.split(left_bracket, 1)
            before_brackets = splitted_text[0]
            after_brackets = splitted_text[1].split(right_bracket, 1)[1]
            text = " ".join((before_brackets, after_brackets))

    for left_bracket in ('(', '[', '{'):
        if left_bracket in text:
            text = text.split(left_bracket, 1)[0]
    return text.strip()


def clear_text(text: str) -> str:
    return text.replace('\n', ' ')\
               .split(':', 1)[1]\
               .strip()


def get_questions_with_answers(question_file: Path) -> dict:
    with open(question_file, 'r') as stream:
        questions_with_answers = json.load(stream)
    return questions_with_answers


def get_questions_list(questions_with_answers: dict) -> list:
    return list(questions_with_answers.keys())


def main() -> None:
    env = Env()
    env.read_env()

    all_questions_file = Path(
        env.str('ALL_QUESTIONS_FILE', 'questions.json')
    )
    question_files = Path(
        env.str('QUESTIONS_DIRECTORY', 'questions/')
    ).glob('*.txt')

    questions_with_answers = {}
    for file in question_files:
        with open(file, 'r', encoding='KOI8-R') as stream:
            file_content = stream.read().split('\n\n')

        current_question = None
        current_answer = None
        for line in file_content:
            if re.match(r'(\n)?Вопрос \d+:\n', line):
                current_question = clear_text(line)
            elif re.match(r'Ответ:\n', line):
                current_answer = clear_text(line)
                if current_question is not None:
                    questions_with_answers[current_question] = current_answer
                current_question = current_answer = None

    with open(all_questions_file, 'w', encoding='utf-8') as stream:
        stream.write(
            json.dumps(questions_with_answers, ensure_ascii=False, indent=2)
        )


if __name__ == '__main__':
    main()
