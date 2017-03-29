declare variable $dataset external;

<output>
{
let $data := $dataset/input
return string($data)
}
</output>
