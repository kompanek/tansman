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
leads to diminishing returns. It can also lead to the reinforcement of bad habits. 
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

In addition to the report and presentation, deliverables will include:

* A Python module implementing the underlying model
* A Jupyter notebook with examples

## Practical application

In imagine that the use of the scheduler will be the context
of a work flow that looks something like this:

1. User breaks up the tasks to be completed into logical
   groupings. Each grouping represent a set of tasks 
   that the user wants to bring to the next level. 
1. Goal is to reach "next level" of competence for each of
   the items. For example, this might be memorizing 
   a particular passage, working out an interpretation of a 
   passage, or addressing a particular techncial challenge.
1. User specifies time available on particular days,
    descriptions of items,
   and estimates of time requirements and other features. T
1. The user generates and schedule and iterates on above.

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

* "Practice Planner: A Journal of Goals and Progress". Harvey R Snitkin

* "The Art of Practicing". Madeline Bruser.

* "On Practicing: A manual for students of guitar performance". Ricardo Iznaola. Not really
  much more than a pamphlet but a pretty good summary of challenges and approaches. 
  Defines distribution of practice time: Building time, interpretive time, performing time, allocation of 
  time during sessions. Recommends 2-3 hours per day for college-level professional students,
  and has other useful distinctions in a section on "Time-Allocation of Materials".
