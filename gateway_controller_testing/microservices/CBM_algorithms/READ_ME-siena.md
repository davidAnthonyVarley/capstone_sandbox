This contains an implementation of the "counting method" as described in "Index structures for selective dissemination of information under the Boolean model" (1993) by tak yan and hector garcia-molina,
with some extra steps for range based predicates, like "price < 30".

This was used in many papers, such as SIENA (2001)

Because these papers are from the 1990s/2000s, there actually isn't a lot of O-S support for these, and since it's not super complicated, I'm just implementing it myself

actually siena 2001 has a repo from carzaniga, i'll see if that works