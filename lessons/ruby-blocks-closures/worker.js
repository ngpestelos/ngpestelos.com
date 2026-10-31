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
      class LessonOutputLimit < StandardError; end
      class LessonOutput
        MAX_BYTES = 16_384
        attr_reader :string

        def initialize
          @string = +""
        end

        def write(value)
          value = value.to_s
          remaining = MAX_BYTES - @string.bytesize
          if value.bytesize > remaining
            @string << value.byteslice(0, remaining).to_s
            raise LessonOutputLimit
          end
          @string << value
          value.bytesize
        end

        def puts(*values)
          values = [nil] if values.empty?
          values.each do |value|
            if value.is_a?(Array)
              value.each { |item| puts(item) }
            else
              text = value.nil? ? "" : value.to_s
              write(text)
              write("\\n") unless text.end_with?("\\n")
            end
          end
          nil
        end

        def print(*values)
          values.each { |value| write(value) }
          nil
        end

        def <<(value)
          write(value)
          self
        end

        def flush; self; end
        def tty?; false; end
      end
      output = LessonOutput.new
      previous_stdout, previous_stderr = $stdout, $stderr
      begin
        $stdout = $stderr = output
        eval(JS.global[:__lesson_code].to_s, TOPLEVEL_BINDING, "lesson.rb")
        output.string
      rescue LessonOutputLimit
        output.string.scrub + "\\n[Output limit reached: 16 KB.]"
      rescue Exception => error
        message = error.message.to_s.byteslice(0, 1024).to_s.scrub
        output.string.scrub + "#{error.class}: #{message}\\n"
      ensure
        $stdout, $stderr = previous_stdout, previous_stderr
      end
    `).toString();
    self.postMessage({ type: 'result', text: result || '(No output)' });
  } catch (error) {
    self.postMessage({ type: 'error', text: `Ruby could not start: ${error.message}. You can still read the examples and expected output.` });
  }
};
