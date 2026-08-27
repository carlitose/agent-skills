---
name: wait-what
description: "Stop. That last message did not land: re-pitch it. Re-explains the previous answer in the controlled-language standard that matches the conversation language (ASD-STE100 for English, plain-language profiles for Italian and Spanish)."
argument-hint: "Which part didn't land? (optional)"
disable-model-invocation: true
---

# Wait, What

The user did not understand the previous message. Re-pitch it.

Owns: one re-explanation of content that is already on the table.

## Boundaries

This skill changes **how** the last answer is said, not **what** it says. Do not use it to
revise a conclusion, add scope, run new tools, or start new work. If the last answer was
actually wrong, say so in one sentence and then re-pitch the corrected version — do not
re-audit the mistake.

Do not apologise, do not open with a preamble, and do not blame the user for missing it.
Do not say the same sentences louder: change the framing, and add a concrete example or a
number the first version lacked.

## 1. Pick the language

Write in the language the **user** writes in — not the language of the message that failed.

1. If the invocation argument names a language, use that.
2. Otherwise use the language of the user's most recent message.
3. Mixed messages: use the dominant language of that message.

Then load the matching profile below. For any language with no profile, apply the
[shared core](#2-shared-core-iso-24495-1) only.

## 2. Shared core (ISO 24495-1)

These come from ISO 24495-1:2023 *Plain language — Governing principles*, and hold in every
language. Its four principles: the reader gets what they need, finds it, understands it, and
can use it.

- Reader first. Open with what the reader must decide or do, not with background.
- One idea per sentence. One topic per paragraph.
- Active voice with an explicit agent.
- Concrete, high-frequency words. No abstraction where an example fits.
- One term per concept, every time. No elegant variation, no synonym for the same thing.
- Define a term inline on first use, in seven words or fewer.
- Expand every acronym on first use.
- Cut filler, stacked hedges, and meta-narration ("as mentioned above", "it is worth noting").
- Put the condition before the instruction.

## 3. Language profiles

### English — ASD-STE100 Simplified Technical English

The real standard. Follow its writing rules and the spirit of its approved dictionary.

- Approved words only, one approved meaning per word. Technical names and technical verbs of
  the domain are allowed.
- Maximum 20 words per procedural sentence, 25 per descriptive sentence.
- Maximum 6 sentences per procedural paragraph.
- Imperative for instructions. One instruction per sentence.
- Simple tenses only: simple present, simple past, simple future.
- No `-ing` verb forms and no gerund chains.
- No noun cluster longer than 3 words.
- Keep the articles. Do not write telegraphic text.
- Write "You must ..." for a requirement, "You can ..." for an option.

### Italiano — ISO 24495-1 + Nuovo vocabolario di base + Gulpease

ASD-STE100 non si traduce: il suo nucleo è un dizionario di parole inglesi approvate e regole
di grammatica inglese. L'equivalente funzionale in italiano è il vocabolario di base come
lessico approvato, più le regole di scrittura amministrativa chiara.

- Lessico: parole del *Nuovo vocabolario di base* (De Mauro), preferendo fondamentale e alto uso.
- Massimo 20-25 parole per frase. Una principale, al massimo una subordinata.
- Voce attiva. Evita il passivo e l'impersonale: "si procede a", "viene effettuato".
- Sciogli le nominalizzazioni: "effettuare la verifica" → "verificare"; "in fase di
  attivazione" → "quando attivi".
- Elimina il burocratese: "al fine di" → "per"; "in ordine a" → "su"; "suddetto/predetto" →
  ripeti il nome; "ovvero" (ambiguo) → "o" oppure "cioè".
- Indicativo presente. Congiuntivo solo se serve davvero.
- Nessuna doppia negazione: "non è escluso che" → "può".
- Anglicismi solo se sono il termine reale del dominio, e glossali la prima volta.
- Rivolgiti al lettore con "tu", sempre lo stesso trattamento.
- Obiettivo di leggibilità: indice Gulpease ≥ 60.

### Español — ISO 24495-1 + lenguaje claro

Mismo criterio: no se traduce ASD-STE100, se aplican sus principios con las normas propias
del español. Si el usuario pide simplificación máxima, sube al nivel de lectura fácil
(UNE 153101:2018 EX).

- Léxico común y concreto. Evita cultismos y fórmulas jurídicas: "el mismo", "dicho",
  "a tenor de", "en aras de", "sin perjuicio de".
- Máximo 20-25 palabras por frase. Una idea por frase.
- Voz activa con agente explícito. Evita la pasiva refleja: "se procederá a realizar" →
  "haremos" o "haz".
- Deshaz las nominalizaciones: "realizar la comprobación de" → "comprobar".
- Evita el gerundio de posterioridad y las perífrasis: "está funcionando" → "funciona".
- Presente de indicativo. Imperativo para las instrucciones.
- Trato consistente: "tú" por defecto, "usted" solo si el usuario lo usa. Nunca mezclados.
- Objetivo de legibilidad: escala INFLESZ / Fernández Huerta ≥ 60 ("bastante fácil").

## 4. Output shape

Four short blocks, headed in the chosen language. No more than roughly 150 words in total.

1. **Where we are** — one or two sentences of context: what we were doing and why this came up.
2. **The point** — the claim, decision, or finding in one sentence.
3. **How it works** — three to five short bullets, or one concrete example with real values.
4. **What I need from you** — the decision or the next action. Omit this block if there is none.

If one specific part was named in the invocation argument, spend blocks 2 and 3 on that part
only.

## 5. Before / after

| Language | Before | After |
|---|---|---|
| EN | "Given that the token would be being validated upstream, the request-scoping behaviour is arguably a non-issue." | "Apigee validates the token first. The API never sees an invalid token. You do not have to change the request scope." |
| IT | "Si procede all'effettuazione della verifica al fine di garantire la corretta valorizzazione del campo." | "Verifichiamo il campo per essere sicuri che il valore sia giusto." |
| ES | "Se procederá a la realización de la comprobación de los datos sin perjuicio de lo dispuesto anteriormente." | "Comprobamos los datos. Lo dicho antes sigue valiendo." |

## 6. Checklist before sending

- The language matches the user's last message.
- Every sentence is under the word limit for that profile.
- No passive or impersonal construction survived.
- Every term appears with the same word each time.
- Every acronym and jargon term is defined on first use.
- There is one concrete example, number, or file path.
- The conclusion is the same one as before, or the change is stated in one sentence.
