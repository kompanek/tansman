# Tansman music practice scheduler tool

For this project, I will build an LP-based optimal scheduling tool for music practice using
Pulp. 

My models will be documented in [Models.ipynb](Models.ipynb).

The corresponding code (such as it is) is in [models.py](models.py).

# Problem and Motivation

Every musician, professional and amateur alike, has faced the challenge of
making efficient use of practice time. In the course of learning a long, complex
piece of music, we can easily fall into patterns where we know that we're not
making the the most efficient use of practice time. One way in which we can make better use of
our time is of course planning up front. This project is about building a system
for generating a schedule automatically given some information about a set of
practice items, the time available and parameters that feed a 
simple personalized utility function.

The work is motivated by trying to address several types of traps encountered when
trying to establish a practice regime:

* The "over-commitment" trap. It's easy when confronted with a large piece not to
appreciate the amount of calendar time required, especially given the
need to take breaks.

* The "ineffective repetition" trap. A particular difficult passage often requires
a large number of short sessions. Spending too much time at one sitting quickly
leads to diminishing returns. It can also lead to the reinforcement of bad happens. 
A particular engaging and/or easy section can lead to a similar pattern.

* The "insufficient reinforcement" trap. In this
case, you make progress on a particular section, and move onto another, but fail
to revisit the original piece within a sufficient period of time. This can lead
to having to re-learn a passage.

The theoretical model motivating this is the "spaced repetition" learning model 
that underlies the approach taken by tools like DuoLingo. In this project,
I won't be implementing spaced repetition training system, but the goal is to
draw from some of the same principles.

# Data

I'll build a set of models that are used to evaluate the features of the 
formulation, as well as a small model of an actual piece that I'm learning.
This will involve some estimation of the practice time required based
on past experience, and subjective assessments of what constitutes a good
practice experience. The inputs will include:

* Time available per session to practice, and number of sessions each day
* An estimate of time needed to master each practice item (e.g., phrase or passage)
* A way to related items it's beneficial to practice together in the same session
* Overall time available for a set of related items (e.g., a section of music)
* Characterization of the intensity, fun, etc. associated with items
* Ideal amount of time to wait between practicing each item (for memory consolidation)
* Maximum time to wait between sessions practicing each item (forgetting)

# Deliverables

In addition to the required presentation, deliverables will include:

* A Python module implementing the underlying model
* A Jupyter notebook with examples

# Overall concept

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

## References

* "Unbounded Human Learning: Optimal Scheduling for Spaced Repetition", Reddy,
et al. This is a pretty sophisticated way of doing things. Can I do something
using LP or mixed IP that approximates this?

* Nice little write up on spaced repetition. 
  http://blog.pickcrew.com/the-science-of-learning-new-languages/

* The wikipedia page on spaced repetition.
  https://en.wikipedia.org/wiki/Spaced_repetition

* http://pianopracticeassistant.com/spaced-repetition/
