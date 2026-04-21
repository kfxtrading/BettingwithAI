"""Out-Of-Domain (OOD) seed utterances for the support intent classifier.

Hand-curated per-language seed bank for training a dedicated ``__ood__``
rejection class. Covers common off-topic queries (weather, food, medical,
generic greetings, random conversation) plus a handful of in-domain-adjacent
ID-OOS examples (betting-ish but *not* covered by any of the 268 intents).

The seeds are intentionally short and deterministic. Scaling to several
hundred OOD rows per language is handled by the M2 ``augment_faq`` pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from football_betting.config import SUPPORT_CFG


@dataclass(frozen=True, slots=True)
class OODSeed:
    text: str
    kind: str  # "ood_generic" | "id_oos"


# ──────────────────────────── Seed utterances ────────────────────────────
#
# Each list has ~30 entries covering:
#   - small talk / greetings / thanks
#   - weather, food, travel, entertainment
#   - medical / legal / tech-support (unrelated)
#   - a few ID-OOS ("sounds like betting but unsupported")

_EN: Final[tuple[OODSeed, ...]] = (
    OODSeed("hello there", "ood_generic"),
    OODSeed("good morning", "ood_generic"),
    OODSeed("thanks a lot", "ood_generic"),
    OODSeed("how are you doing today", "ood_generic"),
    OODSeed("what is the weather in berlin", "ood_generic"),
    OODSeed("will it rain tomorrow", "ood_generic"),
    OODSeed("recipe for carbonara", "ood_generic"),
    OODSeed("best pizza near me", "ood_generic"),
    OODSeed("book a flight to madrid", "ood_generic"),
    OODSeed("translate this to french", "ood_generic"),
    OODSeed("play some music", "ood_generic"),
    OODSeed("what time is it", "ood_generic"),
    OODSeed("who won the oscars", "ood_generic"),
    OODSeed("what is the capital of brazil", "ood_generic"),
    OODSeed("i have a headache", "ood_generic"),
    OODSeed("how do i reset my router", "ood_generic"),
    OODSeed("set an alarm for 7am", "ood_generic"),
    OODSeed("tell me a joke", "ood_generic"),
    OODSeed("what is 12 times 17", "ood_generic"),
    OODSeed("is the train on time", "ood_generic"),
    OODSeed("order a taxi", "ood_generic"),
    OODSeed("who are you", "ood_generic"),
    OODSeed("recommend a good book", "ood_generic"),
    OODSeed("stop talking", "ood_generic"),
    OODSeed("nevermind", "ood_generic"),
    # ID-OOS: sounds betting-ish but not covered
    OODSeed("can i bet on tennis here", "id_oos"),
    OODSeed("do you support horse racing tips", "id_oos"),
    OODSeed("what is the lottery jackpot", "id_oos"),
    OODSeed("how do i trade crypto", "id_oos"),
    OODSeed("give me stock market picks", "id_oos"),
)

_DE: Final[tuple[OODSeed, ...]] = (
    OODSeed("hallo zusammen", "ood_generic"),
    OODSeed("guten morgen", "ood_generic"),
    OODSeed("danke dir", "ood_generic"),
    OODSeed("wie geht es dir heute", "ood_generic"),
    OODSeed("wie ist das wetter in berlin", "ood_generic"),
    OODSeed("regnet es morgen", "ood_generic"),
    OODSeed("rezept fuer spaghetti carbonara", "ood_generic"),
    OODSeed("beste pizzeria in der naehe", "ood_generic"),
    OODSeed("flug nach madrid buchen", "ood_generic"),
    OODSeed("uebersetze das ins englische", "ood_generic"),
    OODSeed("spiel mir musik", "ood_generic"),
    OODSeed("wie spaet ist es", "ood_generic"),
    OODSeed("wer hat den oscar gewonnen", "ood_generic"),
    OODSeed("was ist die hauptstadt von brasilien", "ood_generic"),
    OODSeed("ich habe kopfschmerzen", "ood_generic"),
    OODSeed("wie starte ich meinen router neu", "ood_generic"),
    OODSeed("stell einen wecker auf 7 uhr", "ood_generic"),
    OODSeed("erzaehl mir einen witz", "ood_generic"),
    OODSeed("was ist 12 mal 17", "ood_generic"),
    OODSeed("faehrt der zug puenktlich", "ood_generic"),
    OODSeed("bestell mir ein taxi", "ood_generic"),
    OODSeed("wer bist du", "ood_generic"),
    OODSeed("empfiehl mir ein buch", "ood_generic"),
    OODSeed("hoer auf zu reden", "ood_generic"),
    OODSeed("vergiss es", "ood_generic"),
    OODSeed("kann ich hier auf tennis wetten", "id_oos"),
    OODSeed("gibt es tipps fuer pferderennen", "id_oos"),
    OODSeed("wie hoch ist der lotto jackpot", "id_oos"),
    OODSeed("wie handle ich krypto waehrungen", "id_oos"),
    OODSeed("gib mir aktien tipps", "id_oos"),
)

_ES: Final[tuple[OODSeed, ...]] = (
    OODSeed("hola a todos", "ood_generic"),
    OODSeed("buenos dias", "ood_generic"),
    OODSeed("muchas gracias", "ood_generic"),
    OODSeed("como estas hoy", "ood_generic"),
    OODSeed("que tiempo hace en madrid", "ood_generic"),
    OODSeed("va a llover manana", "ood_generic"),
    OODSeed("receta de paella", "ood_generic"),
    OODSeed("mejor pizzeria cerca", "ood_generic"),
    OODSeed("reservar vuelo a berlin", "ood_generic"),
    OODSeed("traduce esto al ingles", "ood_generic"),
    OODSeed("pon musica", "ood_generic"),
    OODSeed("que hora es", "ood_generic"),
    OODSeed("quien gano el oscar", "ood_generic"),
    OODSeed("cual es la capital de brasil", "ood_generic"),
    OODSeed("me duele la cabeza", "ood_generic"),
    OODSeed("como reinicio el router", "ood_generic"),
    OODSeed("pon una alarma a las 7", "ood_generic"),
    OODSeed("cuentame un chiste", "ood_generic"),
    OODSeed("cuanto es 12 por 17", "ood_generic"),
    OODSeed("llega puntual el tren", "ood_generic"),
    OODSeed("pide un taxi", "ood_generic"),
    OODSeed("quien eres tu", "ood_generic"),
    OODSeed("recomiendame un libro", "ood_generic"),
    OODSeed("deja de hablar", "ood_generic"),
    OODSeed("olvidalo", "ood_generic"),
    OODSeed("puedo apostar al tenis aqui", "id_oos"),
    OODSeed("dais pronosticos de carreras de caballos", "id_oos"),
    OODSeed("cual es el premio de la loteria", "id_oos"),
    OODSeed("como opero con criptomonedas", "id_oos"),
    OODSeed("dame recomendaciones de bolsa", "id_oos"),
)

_FR: Final[tuple[OODSeed, ...]] = (
    OODSeed("bonjour a tous", "ood_generic"),
    OODSeed("bonjour", "ood_generic"),
    OODSeed("merci beaucoup", "ood_generic"),
    OODSeed("comment vas tu aujourd hui", "ood_generic"),
    OODSeed("quel temps fait il a paris", "ood_generic"),
    OODSeed("va t il pleuvoir demain", "ood_generic"),
    OODSeed("recette de la carbonara", "ood_generic"),
    OODSeed("meilleure pizzeria pres de moi", "ood_generic"),
    OODSeed("reserver un vol pour madrid", "ood_generic"),
    OODSeed("traduis cela en anglais", "ood_generic"),
    OODSeed("mets de la musique", "ood_generic"),
    OODSeed("quelle heure est il", "ood_generic"),
    OODSeed("qui a gagne l oscar", "ood_generic"),
    OODSeed("quelle est la capitale du bresil", "ood_generic"),
    OODSeed("j ai mal a la tete", "ood_generic"),
    OODSeed("comment redemarrer le routeur", "ood_generic"),
    OODSeed("mets un reveil a sept heures", "ood_generic"),
    OODSeed("raconte moi une blague", "ood_generic"),
    OODSeed("combien font 12 fois 17", "ood_generic"),
    OODSeed("le train est il a l heure", "ood_generic"),
    OODSeed("commande un taxi", "ood_generic"),
    OODSeed("qui es tu", "ood_generic"),
    OODSeed("recommande moi un livre", "ood_generic"),
    OODSeed("arrete de parler", "ood_generic"),
    OODSeed("laisse tomber", "ood_generic"),
    OODSeed("puis je parier sur le tennis ici", "id_oos"),
    OODSeed("donnez vous des pronostics hippiques", "id_oos"),
    OODSeed("quel est le jackpot du loto", "id_oos"),
    OODSeed("comment trader des cryptos", "id_oos"),
    OODSeed("donne moi des conseils boursiers", "id_oos"),
)

_IT: Final[tuple[OODSeed, ...]] = (
    OODSeed("ciao a tutti", "ood_generic"),
    OODSeed("buongiorno", "ood_generic"),
    OODSeed("grazie mille", "ood_generic"),
    OODSeed("come stai oggi", "ood_generic"),
    OODSeed("che tempo fa a roma", "ood_generic"),
    OODSeed("pioverà domani", "ood_generic"),
    OODSeed("ricetta della carbonara", "ood_generic"),
    OODSeed("migliore pizzeria vicino a me", "ood_generic"),
    OODSeed("prenota un volo per madrid", "ood_generic"),
    OODSeed("traduci questo in inglese", "ood_generic"),
    OODSeed("metti della musica", "ood_generic"),
    OODSeed("che ore sono", "ood_generic"),
    OODSeed("chi ha vinto l oscar", "ood_generic"),
    OODSeed("qual è la capitale del brasile", "ood_generic"),
    OODSeed("ho mal di testa", "ood_generic"),
    OODSeed("come riavvio il router", "ood_generic"),
    OODSeed("imposta una sveglia alle 7", "ood_generic"),
    OODSeed("raccontami una barzelletta", "ood_generic"),
    OODSeed("quanto fa 12 per 17", "ood_generic"),
    OODSeed("il treno è in orario", "ood_generic"),
    OODSeed("chiama un taxi", "ood_generic"),
    OODSeed("chi sei", "ood_generic"),
    OODSeed("consigliami un libro", "ood_generic"),
    OODSeed("smettila di parlare", "ood_generic"),
    OODSeed("lascia stare", "ood_generic"),
    OODSeed("posso scommettere sul tennis qui", "id_oos"),
    OODSeed("date pronostici sulle corse di cavalli", "id_oos"),
    OODSeed("quanto vale il jackpot del lotto", "id_oos"),
    OODSeed("come faccio trading in cripto", "id_oos"),
    OODSeed("dammi consigli in borsa", "id_oos"),
)

_BY_LANG: Final[dict[str, tuple[OODSeed, ...]]] = {
    "en": _EN,
    "de": _DE,
    "es": _ES,
    "fr": _FR,
    "it": _IT,
}


def get_seed_bank(lang: str) -> tuple[OODSeed, ...]:
    """Return the curated OOD seed utterances for ``lang``.

    Raises ``KeyError`` for unknown languages (caller should check against
    ``SUPPORT_CFG.languages`` first).
    """
    return _BY_LANG[lang]


def build_ood_rows(lang: str) -> list[dict[str, object]]:
    """Materialize OOD seeds as dataset rows compatible with the JSONL loader.

    Each row mirrors the schema of ``dataset_augmented.jsonl`` (``id``,
    ``lang``, ``chapter``, ``question``, ``source``) with the sentinel intent
    id / chapter coming from :data:`SUPPORT_CFG.ood_label` /
    :data:`SUPPORT_CFG.ood_chapter`.
    """
    cfg = SUPPORT_CFG
    seeds = get_seed_bank(lang)
    rows: list[dict[str, object]] = []
    for i, seed in enumerate(seeds):
        rows.append(
            {
                "id": cfg.ood_label,
                "key": "support.ood",
                "chapter": cfg.ood_chapter,
                "lang": lang,
                "question": seed.text,
                "answer": "",
                "tags": [],
                "source": f"ood_seed:{seed.kind}",
                "variant": i,
            }
        )
    return rows


__all__ = ["OODSeed", "build_ood_rows", "get_seed_bank"]
