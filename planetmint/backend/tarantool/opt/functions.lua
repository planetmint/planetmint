local fiber = require('fiber')

local export = {}

function export.atomic(batch_size, iter, fn)
    box.atomic(function()
        local i = 0
        for _, x in iter:unwrap() do
            fn(x)
            i = i + 1
            if i % batch_size == 0 then
                box.commit()
                fiber.yield() -- for read-only operations when `commit` doesn't yield
                box.begin()
            end
        end
    end)
end

return export