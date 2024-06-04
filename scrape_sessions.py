from dataclasses import dataclass
import datetime
import typing
import ipdb
import logging
import pydantic
import pprint
import os
import urllib.parse
import requests

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")


@dataclass
class Config:
    requests: requests.Session
    api_url: str
    language: str


def get_config() -> Config:
    api_url = os.getenv("SESSIONS_API_URL")
    assert api_url

    api_key = os.getenv("SESSIONS_API_KEY")
    assert api_key

    session = requests.Session()
    session.headers = {"X-API-Key": api_key}

    return Config(api_url=api_url, requests=session, language="nl")


class Session(pydantic.BaseModel):
    id: str
    name: str
    actualStart: datetime.datetime
    transcriptionActive: bool
    sessionLink: str

    # Example response:
    # {
    #   "id": "string",
    #   "name": "string",
    #   "lifecycle": "NOT_STARTED",
    #   "sendEmailsAutomatically": true,
    #   "requestPermissionToJoin": false,
    #   "startAt": "2024-06-04T11:18:29.125Z",
    #   "plannedEnd": "2024-06-04T11:18:29.125Z",
    #   "actualStart": "2024-06-04T11:18:29.125Z",
    #   "endedAt": "2024-06-04T11:18:29.125Z",
    #   "occurrenceId": "2024-06-04T11:18:29.125Z",
    #   "order": 0,
    #   "allowMicrophoneType": "EVERYONE",
    #   "description": "string",
    #   "timeZone": "Europe/Bucharest",
    #   "autopilot": true,
    #   "endByWorker": true,
    #   "createdAt": "2024-06-04T11:18:29.125Z",
    #   "updatedAt": "2024-06-04T11:18:29.125Z",
    #   "quickSession": false,
    #   "timeDependency": false,
    #   "allowScreenShareType": "EVERYONE",
    #   "enableReactionsType": "EVERYONE",
    #   "transcriptionActive": false,
    #   "source": "APP",
    #   "isChildOfBreakoutRooms": false,
    #   "askForGuestEmail": false,
    #   "showAgendaInLobby": true,
    #   "allowCameraType": "EVERYONE",
    #   "hideNonStreamingParticipants": false,
    #   "autoRecording": false,
    #   "recordingType": "RECORDING",
    #   "livestreamOutputUrls": [
    #     "string"
    #   ],
    #   "memoryAccessType": "JUST_ATTENDEES",
    #   "allowAgendaType": "EVERYONE",
    #   "reminders": {},
    #   "sessionLink": "string"
    # }


Sessions = typing.List[Session]


class TranscriptContent(pydantic.BaseModel):
    language: str
    text: str


class TranscriptElement(pydantic.BaseModel):
    participantId: str
    sourceTimestamp: datetime.datetime

    content: list[TranscriptContent]

    #   {'content': [{'id': 'b9122954-232c-4fdf-8553-25461ec8a577',
    #              'isOriginal': True,
    #              'language': 'nl',
    #              'text': 'Maar draait het op dit moment? Want de laatste keer '
    #                      'dat ik checkte, draaide het niet, dus dan wordt het '
    #                      'ook moeilijk om met het programma te werken.  De app.  '
    #                      'Nee.  Dat is het database probleem waar ik '
    #                      'persoonlijk, ik schaam me er een beetje voor bijna. '
    #                      'Het hoort gewoon niet, weet je.',
    #              'transcriptId': '91ab7f25-ad98-4c07-b732-2629124e1ffb'}],
    # 'id': '91ab7f25-ad98-4c07-b732-2629124e1ffb',
    # 'participantId': 'd6deda7e-4ea1-42ba-9e6a-1c95de38df63',
    # 'sessionId': '276e1583-957f-4823-8472-789c1d368539',
    # 'sourceLanguage': 'nl',
    # 'sourceTimestamp': '2024-05-09T18:04:18.826Z'}


Transcript = typing.List[TranscriptElement]


class ParticipantUser(pydantic.BaseModel):
    id: str
    email: str
    firstName: str
    lastName: str


class Participant(pydantic.BaseModel):
    user = ParticipantUser
    guest = ParticipantUser
    # {
    #   "id": "string",
    #   "lastSeenTimestamp": "2024-06-04T13:45:11.200Z",
    #   "lastChimePresenceTs": "string",
    #   "muted": false,
    #   "isOwner": false,
    #   "isAssistant": false,
    #   "conferenceStatus": "PARTICIPANT",
    #   "changedBy": "OWNER",
    #   "isApproved": false,
    #   "mockedParticipant": false,
    #   "status": "NOT_JOINED",
    #   "invitedByTheOwner": false,
    #   "hasAttendedSession": false,
    #   "inviteStatus": "NEEDS_ACTION",
    #   "presenceHistory": {},
    #   "connectionId": "string",
    #   "source": "APP",
    #   "createdAt": "2024-06-04T13:45:11.200Z",
    #   "updatedAt": "2024-06-04T13:45:11.200Z",
    #   "controlStatus": "CONTROLLING",
    #   "isRecorder": false,
    #   "askToUnmute": false,
    #   "askToStartCamera": false,
    #   "user": {
    #     "id": "string",
    #     "email": "string",
    #     "firstName": "string",
    #     "lastName": "string"
    #   },
    #   "guest": {
    #     "id": "string",
    #     "email": "string",
    #     "firstName": "string",
    #     "lastName": "string"
    #   }
    # }


Participants = typing.List[Participant]


def get_sessions(config: Config) -> Sessions:
    url = urllib.parse.urljoin(config.api_url, "/api/sessions/")
    resp = config.requests.get(url)

    sessions = [Session.parse_obj(item) for item in resp.json()]

    return sessions


def get_participant(config: Config, elem: TranscriptElement) -> Participant:
    url = urllib.parse.urljoin(
        config.api_url, f"/api/sessions/{elem.participantId}/participants"
    )

    resp = config.requests.get(url)

    assert resp.status_code == 200

    return Participant.parse_obj(resp.json())


def get_transcript(config: Config, session: Session) -> Transcript:
    print(f"Getting session: {session.name} transcript:")

    url = urllib.parse.urljoin(
        config.api_url, f"/api/sessions/{session.id}/transcripts"
    )

    resp = config.requests.get(url)
    assert resp.status_code == 200

    transcription_elements = [TranscriptElement.parse_obj(item) for item in resp.json()]

    return transcription_elements


def get_participant_name(participant: Participant) -> str:
    if participant.user:
        return f"{participant.user.firstName}{participant.user.lastName}"

    if participant.guest:
        return f"{participant.guest.firstName}{participant.guest.lastName}"

    assert False


def format_transcription(
    config: Config, transcript: Transcript, participants: Participants
) -> str:
    output = []

    for element in transcript:
        participant = get_participant(config, element)
        participant_name = get_participant_name(participant)

        text = "\n".join(
            [e.text for e in element.content if e.language == config.language]
        )
        output.append(f"{participant_name}\n{text}")

    return "\n\n".join(output)


def main():
    config = get_config()
    sessions = get_sessions(config)
    # transcribed_sessions = filter(lambda s: s.transcriptionActive, sessions)

    for session in sessions[:1]:
        transcript = get_transcript(config, session)
        participants = []  # get_participants(config, session) 403's

        formatted_transcription = format_transcription(config, transcript, participants)
        print(formatted_transcription)


main()
