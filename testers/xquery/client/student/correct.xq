declare variable $dataset0 external;

<output>
{
let $data := $dataset0/input
return string($data)
}
</output>
