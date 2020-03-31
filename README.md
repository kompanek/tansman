Test:
![formula](https://render.githubusercontent.com/render/math?math=e^{i \pi} = -1)

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

* Time available per day to practice
* Amount of time needed to master an item (e.g., phrase or passage)
* Overall time available for a set of related items (e.g., a section of music)
* The difficulty vs. fun dimensions of a particular task--idea is that
  a practice session should include both practice that feels like a chore
  and more fun/interesting tasks (below use "energy" in a sense of how much
  of a drain it is on enthusiasm. There's probably a better name.)
* Ideal amount of time to wait between practicing a particular item (consolidation)
* Maximum time to wait between sessions practicing a particular item (forgetting)

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

**Indices**
\begin{align*}
i &\in \{0, 1,  \ldots, n_{items}-1 \} \\
t &\in \{0, 1, \ldots, n_{slots}-1 \} \\
t_\delta &\in \{0, 1, \ldots, WINDOWSIZE\}
\end{align*}

See below for the use of $t_\delta$ and $WINDOWSIZE$ to express 
limits on practice "density".

**Data**

\begin{table}[h]
\begin{tabular}{ll}
$n_{items}$             & Number of items to schedule \\
$n_{slots}$             & Number of time slots available \\
$ENERGYUSED_i$          & Amount of mental "energy" required per chunk of practice time for task i \\
$TIMEAVAILABLE_t$       & Time available during a training slot $t$ (chunks per day) \\
$TIMEPERITEM_i$         & Practice time needed to master item $i$ \\
$MINPERWINDOW$  & Minimum number of training slots for item $i$ within a window (days) \\
$MAXPERWINDOW$  & Maximum number of training slots for item $i$ within a window (days) \\
$WINDOWSIZE$            & Used to express minimum and maximum "density" of practice days (days)\\
\end{tabular}
\end{table}


**Variables**
\begin{table}[h]
\begin{tabular}{ll}
$P_{i,t}$              & Amount of practice in time slot $t$ for item $i$ (chunks of study)\\
$ENERGY_{t}$           & Energy expended on a given day (really a macro not a variable)\\
$ENERGYDECREASE_t$     & Amount by which energy expenditure decreased at $t$ from $t-1$\\
$ENERGYINCREASE_t$     & Amount by which energy expenditure increased at $t$ from $t-1$\\
$TIMESOFAR_{i,t}$      & Amount of practice for item $i$ up to and including time $t$\\
\end{tabular}
\end{table}

**Objective**

Minimize

$\sum_{i, t} TIMEPERITEM_i P_{i,t} +$
$\sum_{t=1}{(ENERGYINCREASE_t - ENERGYDECREASE_t)} +$
$\sum_{i,t} TIMESOFAR_{i,t}$

**Constraints**
\begin{align}
& \sum_{i}{P_{i,t}} \leq TIMEAVAILABLE_t\ \forall\ t \tag{C1: No more time allocated to time slot than available} \\
& \sum_{t}{P_{i,t}} \geq TIMEPERITEM_i\   \forall\ i \tag{C2: Practice time greater than required to learn item} \\
& \sum_{i}{P_{i,t + t_\delta}}  \geq MINPERWINDOW\ \forall i, t \forall t_\delta 
  \tag{C3: Practice spacing - minimum amount of practice in window} \\
& \sum_{i}{P_{i,t + t_\delta}}  \leq MAXPERWINDOW\ \forall i, t
  \tag{C4: Practice spacing for rest - maximum amount of practice in window}\\
& TIMESOFAR_{i,t} = \sum_i{\sum_{t0=0 \ldots t}{P_{i,t0}}}\ \forall i,t 
   \tag{C5: Definition. Used in objective to bias toward finishing earlier}\\
& ENERGY_{t} = \sum_i{ENERGYUSED_i \times P_{i,t}}
   \tag{C6: Definition. Used in definition of increase/decrease for smoothing}\\
& ENERGY_{t+1} - ENERGY_{t} = ENERGYINCREASE_{t+1} - ENERGYDECREASE_{t+1}
   \tag{C7: Change in energy to smooth. Minimization means only one non-zero}
\end{align}

Note I had to introduce the $WINDOWSIZE$ parameter in order to have a way
to express (C3) and (C4). Right now this is something that needs
to be specified as part of the configuration of the model. It's a bit
unnatural.

When I first started experimenting I noticed that these constraints could
result in practice schedules "pushed to the right" with low density
slots to the left of the schedule because I had not expressed the 
idea of optimizing the amount of calendar time spent. As a heuristic,
I decided to incorporate another variable: $TIMESOFAR_{i,t}$ defined as the sum
of practice time for each item $i$ up to time $t$. The idea
was to maximize the sum of these times as a "timeliness" metric. It ends
up penalizing late completion for each task.


The time window is sort of awkward and creates some odd scheduling artifacts.
Next I'm going to try different sorts of energy surpluses/deficits. where there
are constraints that prevent it from going too high or too low. For each
practice item a day of rest will deplete the "learning" banked, while a day of
practice will increase it, but only within a threshold. Equivalent to production
smoothing in other problems I've seen.

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
