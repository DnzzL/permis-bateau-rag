/**
 * exam.js — Mode « examen blanc » : correction DIFFÉRÉE (on répond à tout, puis on corrige).
 *
 * À la différence de quiz.js (feedback immédiat), ce composant attend que
 * l'utilisateur clique sur « Corriger » pour révéler les réponses et le score.
 *
 * Structure HTML attendue :
 *   <div id="exam" data-max-errors="5">
 *     <div class="exam-bar" id="exam-progress"><span>…</span><span class="count"></span></div>
 *
 *     <div class="exam-question" data-correct="2" data-topic="Balisage" data-feedback="…">
 *       <p><strong>1.</strong> Question ?</p>
 *       <ul class="quiz-options"><li>A</li><li>B</li><li>C</li><li>D</li></ul>
 *     </div>
 *     …
 *
 *     <button class="exam-btn" id="exam-submit">Corriger l'examen</button>
 *     <div id="exam-results"></div>
 *   </div>
 *
 * data-correct = index (base 0) de la bonne réponse.
 * data-topic   = thème, pour le bilan par chapitre.
 * data-max-errors (sur #exam) = nombre d'erreurs tolérées (défaut 5).
 */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var examRoot = document.getElementById('exam');
    if (!examRoot) return;

    var questions = Array.prototype.slice.call(document.querySelectorAll('.exam-question'));
    var total = questions.length;
    var maxErrors = parseInt(examRoot.getAttribute('data-max-errors') || '5', 10);
    var passNeeded = total - maxErrors;

    var bar = document.getElementById('exam-progress');
    var submitBtn = document.getElementById('exam-submit');
    var results = document.getElementById('exam-results');
    var answers = {}; // qIndex -> selected option index

    function updateCount() {
      if (!bar) return;
      var n = Object.keys(answers).length;
      var el = bar.querySelector('.count');
      if (el) el.textContent = n + ' / ' + total + ' répondues';
    }

    questions.forEach(function (q, qi) {
      var options = q.querySelectorAll('.quiz-options li');

      var fb = document.createElement('div');
      fb.className = 'quiz-feedback';
      fb.textContent = q.getAttribute('data-feedback') || '';
      q.appendChild(fb);

      options.forEach(function (opt, oi) {
        opt.classList.add('quiz-option');
        opt.addEventListener('click', function () {
          if (q.classList.contains('answered')) return; // verrouillé après correction
          options.forEach(function (o) { o.classList.remove('selected'); });
          opt.classList.add('selected');
          answers[qi] = oi;
          updateCount();
        });
      });
    });

    function grade() {
      var nCorrect = 0;
      var byTopic = {};

      questions.forEach(function (q, qi) {
        var options = q.querySelectorAll('.quiz-options li');
        var correctIdx = parseInt(q.getAttribute('data-correct'), 10);
        var topic = q.getAttribute('data-topic') || 'Divers';
        if (!byTopic[topic]) byTopic[topic] = { ok: 0, total: 0 };
        byTopic[topic].total++;

        var sel = answers.hasOwnProperty(qi) ? answers[qi] : -1;
        var isOk = sel === correctIdx;
        if (isOk) { nCorrect++; byTopic[topic].ok++; }

        options.forEach(function (o, oi) {
          o.classList.remove('selected');
          o.style.pointerEvents = 'none';
          if (oi === correctIdx) o.classList.add('correct');
          if (oi === sel && sel !== correctIdx) o.classList.add('wrong');
        });

        var fb = q.querySelector('.quiz-feedback');
        if (fb) {
          var prefix = (sel === -1) ? '⚠️ Sans réponse. ' : '';
          fb.textContent = prefix + (q.getAttribute('data-feedback') || '');
          fb.className = 'quiz-feedback show ' + (isOk ? 'correct' : 'wrong');
        }
        q.classList.add('answered');
      });

      var errors = total - nCorrect;
      var pass = errors <= maxErrors;

      var html = '';
      html += '<div class="exam-result ' + (pass ? 'pass' : 'fail') + '">';
      html += '<div class="score">' + nCorrect + ' / ' + total + '</div>';
      html += '<div class="verdict">' + (pass ? 'ADMIS ✅' : 'RECALÉ ❌') + '</div>';
      html += '<p>' + errors + ' erreur' + (errors > 1 ? 's' : '') +
              ' — il faut au moins <strong>' + passNeeded + ' / ' + total +
              '</strong> (maximum ' + maxErrors + ' erreurs).</p>';
      html += '</div>';

      html += '<h3>Bilan par thème</h3>';
      html += '<table><tr><th>Thème</th><th>Score</th><th>À réviser ?</th></tr>';
      Object.keys(byTopic).forEach(function (t) {
        var b = byTopic[t];
        var ratio = b.ok / b.total;
        var flag = ratio < 0.7 ? '⚠️ oui' : '✅';
        html += '<tr><td>' + t + '</td><td>' + b.ok + ' / ' + b.total + '</td><td>' + flag + '</td></tr>';
      });
      html += '</table>';
      html += '<p class="meta">Les thèmes ⚠️ (moins de 70 % de bonnes réponses) sont vos points faibles : relisez la leçon correspondante puis recommencez.</p>';
      html += '<button class="exam-btn secondary" id="exam-restart">↻ Recommencer l\'examen</button>';

      results.innerHTML = html;
      results.scrollIntoView({ behavior: 'smooth', block: 'start' });

      var restart = document.getElementById('exam-restart');
      if (restart) restart.addEventListener('click', function () { location.reload(); });

      if (submitBtn) { submitBtn.disabled = true; submitBtn.style.display = 'none'; }
    }

    if (submitBtn) {
      submitBtn.addEventListener('click', function () {
        var n = Object.keys(answers).length;
        if (n < total) {
          var msg = 'Il reste ' + (total - n) + ' question(s) sans réponse.\n' +
                    'Corriger quand même ? (Elles compteront comme fausses.)';
          if (!window.confirm(msg)) return;
        }
        grade();
      });
    }

    updateCount();
  });
})();
