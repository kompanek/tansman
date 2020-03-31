# Tansman music practice scheduler tool

An attempt at building an LP-based optimal scheduler for music practice.

# Problem and Motivation

Every musician, professional and amateur alike, has faced the challenge of
making efficient use of practice time. In the course of learning a long, complex
piece of music, we can easily fall into patterns where we know that we're not
making the best of my practice time. One way in which we can make better use of
our time is of course planning up front. This project is about building a system
for generating a schedule automatically given some information about the
practice items, and the time available.

The work is motivated by trying to address several types of traps encountered when
trying to establish a practice regime:

* The "over-commitment" trap. It's easy when confronted with a large piece not to
appreciate the amount of calendar time required, especially given the
requirements of rest for consolidation.

* The "ineffective repetition" trap. The first variation, which I'll "masochistic repetition" is what
happens I'm so fixated on a particular difficult passage that I ignore
everything else even though it's clear the repetition is at best leading to
diminishing returns and at worse simply reinforcing problems. 

* The "hedonistic repetition" trap. This occurs
when I manage to master a small section of music and repeatedly play it because
it satisfies a need to feel good about progress, and perhaps as an avoidance
measure. 

* The "insufficient reinforcement" trap. In this
case, you make progress on a particular section, and move onto another, but fail
to revisit the original piece within a sufficient period of time. Inevitably, I
end up having to relearn the passage. 

The theoretical model motivating this is the "spaced repetition" model in learning.

# Thinking about inputs

* Time available per session to practice
* Number of sessions each day
* An estimate of time needed to master each practice item (e.g., phrase or passage)
* A way to related items it's beneficial to practice together in the same session
* Overall time available for a set of related items (e.g., a section of music)
* The difficulty vs. fun dimensions of a particular task--idea is that
  a practice session should include both practice that feels like a chore
  and more fun/interesting tasks (below use "energy" in a sense of how much
  of a drain it is on enthusiasm. There's probably a better name.)
* Ideal amount of time to wait between practicing each item (consolidation)
* Maximum time to wait between sessions practicing each item (forgetting)

# LP Forumulation #1

# LP model

Focus on finding a reasonable solution that meets constraints capturing some of
those inputs and a larger goal. In particular, given a larger goal--say,
mastering a particular section of a large piece of music--, and set of tasks
that require a certain amount of practice (units of practice time) and entail
certain constraints, a particular amount of calendar time (number of slots), and
a particular amount of time available per slot (units of practice time), is
there a feasible schedule?

* A practice *item* is a chunk of music, technique exercise, etc.
* A time *slot* corresponds to a unit of time like a day or a practice session

The schedule produced is a matrix. The amount of practice time spent 
on a particular task (row) in a particular time slot (column). 

## LP Formulation

See ...

## Practical application

This is applied in the context of a work flow and algorithm like:

1. User breaks up the tasks to be completed into logical
   groupings. Each grouping represent a set of tasks 
   that the user wants to bring to the next level. 
1. Goal is to reach "next level" of competence (which corresponds
   to different parameters, in particular permitting more time to
   pass until an item is revisted and practiced again corresponding
   to a firmer grasp on the material, and natural spacing)
1. User specifies time available per slot, descriptions of items,
   etc.
1. User has choice to runs scheduler tool with an explicit number
   of time slots or have the scheduler iterate into it finds 
   a feasible solution.
1. Schedule is the matrix described, rendered in a meaningful way

I'd also want to update the software to allow names to be assigned
to items, and to map slots to actual dates and times. This is
straightforward. I'd also want to tweak the model to account
for different days having different time available, the notion
of having days off (maybe a day a week), etc.
