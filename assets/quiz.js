/**
 * quiz.js — Interactive quiz widget for Permis Bateau lessons.
 *
 * Usage:
 *   <div class="quiz-question" data-correct="0" data-feedback="Explication ici">
 *     <p>Question text?</p>
 *     <ul class="quiz-options">
 *       <li>Option A</li>
 *       <li>Option B</li>
 *       <li>Option C</li>
 *     </ul>
 *   </div>
 *
 * The data-correct attribute is the zero-based index of the correct answer.
 * The data-feedback attribute is shown after answering.
 *
 * For multiple correct answers, use data-correct="0,2" and add
 * data-multiple="true".
 */

(function() {
  'use strict';

  document.addEventListener('DOMContentLoaded', function() {
    var questions = document.querySelectorAll('.quiz-question');

    questions.forEach(function(q) {
      var options = q.querySelectorAll('.quiz-options li');
      var correctIndices = q.getAttribute('data-correct').split(',').map(Number);
      var feedbackText = q.getAttribute('data-feedback') || '';
      var multiple = q.hasAttribute('data-multiple');

      // Create feedback container
      var feedback = document.createElement('div');
      feedback.className = 'quiz-feedback';
      feedback.textContent = feedbackText;
      q.appendChild(feedback);

      // Style options as clickable
      options.forEach(function(opt, idx) {
        opt.classList.add('quiz-option');

        opt.addEventListener('click', function() {
          var wasSelected = opt.classList.contains('selected');

          if (!multiple) {
            // Single select — deselect all others
            options.forEach(function(o) { o.classList.remove('selected'); });
          }

          if (!multiple && wasSelected) {
            // Toggle off
            opt.classList.remove('selected');
            feedback.classList.remove('show', 'correct', 'wrong');
            return;
          }

          if (!multiple) {
            opt.classList.add('selected');
          } else {
            opt.classList.toggle('selected');
          }

          // In single mode, immediately check
          if (!multiple) {
            var isCorrect = correctIndices.indexOf(idx) !== -1;
            opt.classList.add(isCorrect ? 'correct' : 'wrong');

            feedback.className = 'quiz-feedback show ' + (isCorrect ? 'correct' : 'wrong');
            if (!isCorrect) {
              // Show correct answer
              options.forEach(function(o, i) {
                if (correctIndices.indexOf(i) !== -1) {
                  o.classList.add('correct');
                }
              });
            }

            // Disable further clicks
            options.forEach(function(o) {
              o.style.pointerEvents = 'none';
            });
          } else {
            // Multi-select mode — check on each click
            checkMultiple(q, options, correctIndices, feedback, multiple);
          }
        });
      });

      // For multi-select, add a "Vérifier" button
      if (multiple) {
        var checkBtn = document.createElement('button');
        checkBtn.textContent = 'Vérifier';
        checkBtn.style.marginTop = '0.75rem';
        checkBtn.style.padding = '0.4rem 1rem';
        checkBtn.style.fontFamily = 'Helvetica Neue, Arial, sans-serif';
        checkBtn.style.fontSize = '0.9rem';
        checkBtn.style.cursor = 'pointer';
        checkBtn.style.border = '1px solid #2980b9';
        checkBtn.style.borderRadius = '4px';
        checkBtn.style.background = '#2980b9';
        checkBtn.style.color = 'white';

        q.appendChild(checkBtn);

        checkBtn.addEventListener('click', function() {
          checkMultiple(q, options, correctIndices, feedback, multiple);
          checkBtn.disabled = true;
          checkBtn.style.opacity = '0.6';
          options.forEach(function(o) { o.style.pointerEvents = 'none'; });
        });
      }
    });

    function checkMultiple(q, options, correctIndices, feedback) {
      var allCorrect = true;
      var allSelected = true;

      options.forEach(function(o, i) {
        var isSelected = o.classList.contains('selected');
        var shouldBeSelected = correctIndices.indexOf(i) !== -1;

        if (isSelected !== shouldBeSelected) allCorrect = false;
        if (!isSelected && shouldBeSelected) allSelected = false;

        if (isSelected && shouldBeSelected) o.classList.add('correct');
        else if (isSelected && !shouldBeSelected) o.classList.add('wrong');
        else if (!isSelected && shouldBeSelected) o.classList.add('correct');
      });

      feedback.className = 'quiz-feedback show ' + (allCorrect ? 'correct' : 'wrong');
    }
  });
})();
