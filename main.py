import os
import re


def main():
    files_folder = 'quiz-questions'

    try:
        quiz_files = [
            os.path.join(files_folder, filename)
            for filename in os.listdir(files_folder)
            if os.path.isfile(os.path.join(files_folder, filename))
        ]
        quiz_files.sort()
    except OSError as err:
        print(f'OSError: {err}')
        return False

    quiz_questions = []
    try:
        for quiz_file in quiz_files[:1]:
            with open(quiz_file, 'r', encoding='KOI8-R') as readable_file:
                for line in readable_file:
                    if re.search(r'^Вопрос\s\d+:$', line):
                        search_pattern = ''
                        question = ''
                        while search_pattern != '\n':
                            search_pattern = readable_file.readline()
                            question += search_pattern.replace('\n', ' ')
                        question = question.rstrip()

                        # Method 1 to find answer
                        # while readable_file.readline() != 'Ответ:\n':
                        #     next(readable_file)
                        # answer = readable_file.readline().rstrip()

                    # Method 2 to find answer
                    if re.search(r'^Ответ:$', line):
                        answer = readable_file.readline().rstrip()

                        quiz_questions.append({
                            'Вопрос': question,
                            'Ответ': answer
                        })
    except OSError as err:
        print(f'OSError: {err}')
    else:
        print(quiz_questions)


if __name__ == '__main__':
    main()
