import requests

from integration.constants import BIG_CHAT_API, OUR_API


def search_chat(external_id):
    """Given a chat id from BigChat find the corresponding id from OutApi"""
    response = requests.get(f"{OUR_API}/chats?external_id={external_id}")
    response.raise_for_status()
    response = response.json()

    if len(response) == 1:
        return response[0]["chat_id"]


def search_or_create_agent(advisor_id, logger):
    """
    Given an advisor id from BigChat find the corresponding id from OutApi
    or create the agent if not found
    """
    response = requests.get(f"{BIG_CHAT_API}/advisors/{advisor_id}")
    response.raise_for_status()
    email = response.json()["email_address"]
    name = response.json()["name"]

    response = requests.get(f"{OUR_API}/agents?email={email}")
    response.raise_for_status()

    if response.json():  # if the agent exists
        return response.json()[0]["agent_id"]
    else:  # if not, then create it
        response = requests.post(f"{OUR_API}/agents", json={"name": name, "email": email})
        response.raise_for_status()
        agent_id = response.json()["agent_id"]
        logger.info(f"Create user {agent_id}")
        return agent_id


def search_advisor(conversation_id):
    """get the advisor id for given chat"""
    response = requests.get(f"{BIG_CHAT_API}/conversations/{conversation_id}")
    response.raise_for_status()
    return response.json()["advisor_id"]