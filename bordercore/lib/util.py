import string


def remove_non_ascii_characters(input_string, default="Default"):
    """
    Remove all non ASCII characters from string. If the entire string consists
    of non ASCII characters, return the "default" value.
    """

    output_string = "".join(filter(lambda x: x in string.printable, input_string))

    if not output_string:
        output_string = default

    return output_string


# Putting these two functions here rather than in blob/models.py so
#  that AWS lambdas can easily re-use them

def is_image(file):

    if file:
        _, file_extension = os.path.splitext(str(file))
        if file_extension[1:].lower() in ["gif", "jpg", "jpeg", "png"]:
            return True
    return False


def is_pdf(file):

    if file:
        _, file_extension = os.path.splitext(str(file))
        if file_extension[1:].lower() in ["pdf"]:
            return True
    return False
