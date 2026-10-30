// A worker keeps the page responsive while Ruby runs. It is terminated after each run.
self.onmessage = async ({ data }) => {
  try {
    self.postMessage({ type: 'status', text: 'Loading Ruby. The first run may take a moment…' });
    const { DefaultRubyVM } = await import('https://cdn.jsdelivr.net/npm/@ruby/wasm-wasi@2.10.1/dist/browser/+esm');
    const response = await fetch('https://cdn.jsdelivr.net/npm/@ruby/4.0-wasm-wasi@2.10.1/dist/ruby+stdlib.wasm');
    if (!response.ok) throw new Error(`Ruby download failed (${response.status})`);
    const module = await WebAssembly.compile(await response.arrayBuffer());
    const { vm } = await DefaultRubyVM(module);
    self.__lesson_code = data.code;
    const result = vm.eval(`
      require "js"
      require "stringio"
      output = StringIO.new
      previous_stdout, previous_stderr = $stdout, $stderr
      begin
        $stdout = $stderr = output
        eval(JS.global[:__lesson_code].to_s, TOPLEVEL_BINDING, "lesson.rb")
      rescue Exception => error
        output.puts "#{error.class}: #{error.message}"
      ensure
        $stdout, $stderr = previous_stdout, previous_stderr
      end
      output.string
    `).toString();
    self.postMessage({ type: 'result', text: result || '(No output)' });
  } catch (error) {
    self.postMessage({ type: 'error', text: `Ruby could not start: ${error.message}. You can still read the examples and expected output.` });
  }
};
