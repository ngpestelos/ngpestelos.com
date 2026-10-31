const editors = document.querySelectorAll('.exercise');
let activeWorker = null;
let activeExercise = null;
let timer = null;

function stop(message) {
  if (!activeWorker) return;
  activeWorker.terminate();
  activeWorker = null;
  clearTimeout(timer);
  activeExercise.querySelector('.status').textContent = message;
  activeExercise.querySelector('.stop').disabled = true;
  activeExercise = null;
}

for (const exercise of editors) {
  const editor = exercise.querySelector('textarea');
  const initial = editor.value;
  const status = exercise.querySelector('.status');
  const output = exercise.querySelector('.output');
  const stopButton = exercise.querySelector('.stop');
  exercise.querySelector('.run').addEventListener('click', () => {
    stop('Stopped to start another example.');
    output.textContent = '';
    status.textContent = 'Starting Ruby…';
    stopButton.disabled = false;
    let worker;
    try {
      worker = new Worker(new URL('worker.js', import.meta.url), { type: 'module' });
    } catch (error) {
      output.textContent = 'Ruby could not start in this browser. The examples and answers are still available.';
      status.textContent = 'Ruby could not run.';
      stopButton.disabled = true;
      return;
    }
    activeWorker = worker;
    activeExercise = exercise;
    worker.onmessage = ({ data }) => {
      if (worker !== activeWorker) return;
      if (data.type === 'status') { status.textContent = data.text; return; }
      output.textContent = data.text;
      stop(data.type === 'error' ? 'Ruby could not run.' : 'Finished.');
    };
    worker.onerror = () => {
      if (worker !== activeWorker) return;
      output.textContent = 'Ruby could not start. Check your connection and try again.';
      stop('Ruby could not run.');
    };
    timer = setTimeout(() => {
      output.textContent = 'The example took too long. Try a smaller program or run again.';
      stop('Stopped after 30 seconds.');
    }, 30000);
    worker.postMessage({ code: editor.value });
  });
  stopButton.addEventListener('click', () => stop('Stopped.'));
  exercise.querySelector('.reset').addEventListener('click', () => {
    if (activeExercise === exercise) stop('Stopped.');
    editor.value = initial;
    output.textContent = '';
    status.textContent = 'Example reset.';
  });
}
