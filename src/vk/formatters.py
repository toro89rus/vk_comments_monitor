from src.vk.models import Post, Comment, Reply
from config.settings import VK_GROUP_LINK


def format_post(post: Post) -> str:
    shortened_text = f"{post.text[:100]}..."
    link_tag = f"<a href='{VK_GROUP_LINK}_{post.id}'>Пост</a>"
    return f"{link_tag} от {post.created_at}\n{shortened_text}"


def format_comment(comment: Comment) -> str:
    return (
        f"{comment.created_at}\n"
        f"Комментарий от {comment.author.name_gen}\n"
        f"{comment.text}"
    )


def format_reply(reply: Reply) -> str:
    return (
        f"{reply.created_at}\n"
        f"Ответ для {reply.reply_to.name_gen} от {reply.author.name_gen} \n"
        f"{reply.text}"
    )
